"""Analysis module for Databench Python kernel."""

import zmq
import time
import logging


class Analysis(object):
    """Databench's analysis class."""

    def __init__(self):
        pass

    def set_emit_fn(self, emit_fn):
        """Sets what the emit function for this analysis will be."""
        self.emit = emit_fn

    """Events."""

    def on_connect(self):
        logging.debug('on_connect called.')

    def on_disconnect(self):
        logging.debug('on_disconnect called.')


class Meta(object):
    """Class providing Meta information about analyses.

    For Python kernels.

    Args:
        name (str): Name of this analysis.
        import_name (str): Usually the file name ``__name__`` where this
            analysis is instantiated.
        description (str): Usually the ``__doc__`` string of the analysis.
        analysis (Analysis): Analysis class.

    """

    def __init__(self, name, import_name, description, analysis):
        self.name = name
        self.import_name = import_name
        self.description = description
        self.analysis_class = analysis
        self.analysis_instances = {}

        self._init_zmq()
        print 'Language kernel for '+self.name+' initialized.'

    def _init_zmq(self, sub_port=8041):
        """Initialize zmq messaging. Listen on sub_port. This port might at
        some point receive the message to start publishing on a certain
        port, but until then, no publishing."""

        self.zmq_publish = None

        self.zmq_sub = zmq.Context().socket(zmq.SUB)
        self.zmq_sub.connect('tcp://127.0.0.1:'+str(sub_port))
        self.zmq_sub.setsockopt(zmq.SUBSCRIBE, '')

    @staticmethod
    def run_action(analysis, fn_name, message):
        """Executes an action in the analysis with the given message. It
        also handles the start and stop signals in case an action_id
        is given.

        This method is exactly the same as in databench.Analysis.
        """

        # detect action_id
        action_id = None
        if '__action_id' in message:
            action_id = message['__action_id']
            del message['__action_id']

        if action_id:
            analysis.emit('__action', {'id': action_id,
                                       'status': 'start'})

        fn = getattr(analysis, fn_name)

        # Check whether this is a list (positional arguments)
        # or a dictionary (keyword arguments).
        if isinstance(message, list):
            fn(*message)
        elif isinstance(message, dict):
            fn(**message)
        else:
            fn(message)

        if action_id:
            analysis.emit('__action', {'id': action_id,
                                       'status': 'end'})

    def event_loop(self):
        """Event loop."""
        while True:
            msg = self.zmq_sub.recv_json()
            logging.debug('kernel msg: '+str(msg))
            if '__databench_namespace' not in msg or \
               msg['__databench_namespace'] != self.name:
                continue

            del msg['__databench_namespace']
            logging.debug('kernel processing msg')

            if '__analysis_id' in msg and \
               msg['__analysis_id'] not in self.analysis_instances:
                # instance does not exist yet
                logging.debug('kernel creating analysis instance ' +
                              str(msg['__analysis_id']))
                i = self.analysis_class()

                def emit(signal, message):
                    self.emit(signal, message, msg['__analysis_id'])

                i.set_emit_fn(emit)
                self.analysis_instances[msg['__analysis_id']] = i

            # init message
            if 'publish_on_port' in msg and not self.zmq_publish:
                port = msg['publish_on_port']
                self.zmq_publish = zmq.Context().socket(zmq.PUB)
                self.zmq_publish.bind('tcp://127.0.0.1:'+str(port))
                logging.debug('kernel publishing on: tcp://127.0.0.1:' +
                              str(port))

                # wait for slow tcp bind
                time.sleep(0.5)

                # sending hello
                self.zmq_publish.send_json({
                    '__databench_namespace': self.name,
                    'description': self.description,
                })

            if '__analysis_id' not in msg:
                continue

            analysis_id = msg['__analysis_id']
            i = self.analysis_instances[analysis_id]
            if 'message' not in msg or \
               'signal' not in msg['message'] or \
               'message' not in msg['message'] or \
               not hasattr(i, 'on_'+msg['message']['signal']):
                continue

            # standard message
            fn_name = 'on_'+msg['message']['signal']
            logging.debug('kernel processing '+fn_name)
            Meta.run_action(i, fn_name, msg['message']['message'])

    def emit(self, signal, message, analysis_id):
        """Emit signal to main.

        Args:
            signal (str): Name of the signal to be emitted.
            message: Message to be sent.
            analysis_id: Identifies the instance of this analysis.

        """
        logging.debug(
            'backend (namespace='+self.name+', analysis='+str(analysis_id) +
            ', signal='+signal + '): ' + (
                (str(message)[:60] + '...')
                if len(str(message)) > 65
                else str(message)
            )
        )

        if self.zmq_publish:
            self.zmq_publish.send_json({
                '__databench_namespace': self.name,
                '__analysis_id': analysis_id,
                'message': {'signal': signal, 'message': message},
            })
        else:
            logging.debug('zmq_socket_pub not defined yet.')

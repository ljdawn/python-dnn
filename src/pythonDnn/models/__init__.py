import numpy,theano,json
from collections import OrderedDict
import theano.tensor as T
from StringIO import StringIO

class nnet(object):
	"""Abstract class for all Network Models"""
	def __init__(self):
		self.finetune_cost = None
		self.params = [];
		self.delta_params = [];
		self.n_layers = 0;
		self.type = None;
		self.mlp_layer_start = 0 

		# allocate symbolic variables for the data
		self.x = T.matrix('x')  # the data is presented as rasterized images
		self.y = T.ivector('y')  # the labels are presented as 1D vector of [int] labels

		#placeholders
		self.output = None
		self.features = None
		self.features_dim = None
		self.errors = None
		self.finetune_cost = None

		#__Regularization Param
		self.l1_reg = None
		self.l2_reg = None
		self.max_col_norm = None


	def getType(self):
		return self.type

	def pretraining_functions(self, *args, **kwargs):
		"""
		Should be implemeted by derived class
		"""
		raise  NotImplementedError;

	#"Building fine tuning operation "
	def build_finetune_functions(self, train_shared_xy, valid_shared_xy, batch_size):
		"""
		Generates a function `train` that implements one step of
		finetuning and a function `validate` that computes the error on 
		a batch from the validation set 

		:type train_shared_xy: pairs of theano.tensor.TensorType
		:param train_shared_xy: It is a list that contain all the train dataset, 
			pair is formed of two Theano variables, one for the datapoints,
			the other for the labels

		:type valid_shared_xy: pairs of theano.tensor.TensorType
		:param valid_shared_xy: It is a list that contain all the valid dataset, 
			pair is formed of two Theano variables, one for the datapoints,
			the other for the labels

		:type batch_size: int
		:param batch_size: size of a minibatch

		:returns (theano.function,theano.function)
		* A function for training takes minibatch_index,learning_rate,momentum 
		which updates weights,and return error rate
		* A function for validation takes minibatch_indexand return error rate
		
		"""

		(train_set_x, train_set_y) = train_shared_xy
		(valid_set_x, valid_set_y) = valid_shared_xy

		index = T.lscalar('index')  # index to a [mini]batch
		learning_rate = T.scalar('learning_rate',dtype=theano.config.floatX)
		momentum = T.scalar('momentum',dtype=theano.config.floatX)

		# compute the gradients with respect to the model parameters
		gparams = T.grad(self.finetune_cost, self.params)

		# compute list of fine-tuning updates
		updates = OrderedDict()

		for dparam, gparam in zip(self.delta_params, gparams):
			updates[dparam] = momentum * dparam - gparam*learning_rate

		for dparam, param in zip(self.delta_params, self.params):
			updates[param] = param + updates[dparam]

		if self.max_col_norm is not None:
			updates = self.__TrainReg__(updates,self.mlp_layer_start*2)
		
		train_inputs = [index, theano.Param(learning_rate, default = 0.001),
			theano.Param(momentum, default = 0.5)]

		train_fn = theano.function(inputs=train_inputs,
			outputs=self.errors,
			updates=updates,
			givens={
				self.x: train_set_x[index * batch_size:(index + 1) * batch_size],
				self.y: train_set_y[index * batch_size:(index + 1) * batch_size]},
			allow_input_downcast=True);

		valid_fn = theano.function(inputs=[index],
			outputs=self.errors,
			givens={
				self.x: valid_set_x[index * batch_size:(index + 1) * batch_size],
				self.y: valid_set_y[index * batch_size:(index + 1) * batch_size]})

		return train_fn, valid_fn

	def build_test_function(self,test_shared_xy,batch_size):
		"""
		Get Fuction for testing

		:type test_shared_xy: pairs of theano.tensor.TensorType
		:param test_shared_xy: It is a list that contain all the test dataset, 
			pair is formed of two Theano variables, one for the datapoints,
			the other for the labels

		:type batch_size: int
		:param batch_size: size of a minibatch
				
		:returns theano.function
		A function which takes index to minibatch and Generates Label Array and error

		"""
		(test_set_x, test_set_y) = test_shared_xy
		index = T.lscalar('index')  # index to a [mini]batch
		test_fn = theano.function(inputs=[index],
			outputs=[self.errors],
			givens={
				self.x: test_set_x[index * batch_size:(index + 1) * batch_size],
				self.y: test_set_y[index * batch_size:(index + 1) * batch_size]})
		return test_fn
	
	def getLayerOutFunction(self):
		"""
		Get Function for extracting output of each layeer
		:returns theano.function
		A function takes input features 
		"""
		raise  NotImplementedError;
	
	def getFeaturesFunction(self):
		"""
		Get Function for extracting Feature/Bottle neck

		:returns theano.function
		A function takes input features 
		"""
		in_x = self.x.type('in_x');
		fn = theano.function(inputs=[in_x],outputs=self.features,
			givens={self.x: in_x},name='features')#,on_unused_input='warn')
		return fn

	def getLabelFunction(self):
		"""
		Get Function for getting output labels

		:returns theano.function
		A function takes input features 
		"""
		in_x = self.x.type('in_x');
		fn = theano.function(inputs=[in_x],outputs=self.output,
			givens={self.x: in_x},name='labels',
			allow_input_downcast=True)#,on_unused_input='warn')
		return fn
		
	def getScoreFunction(self):
		"""
		Get Function for getting score for each labels

		:returns theano.function
		A function takes input features 
		"""
		in_x = self.x.type('in_x');
		fn = theano.function(inputs=[in_x],outputs=self.logLayer.posterior(),
			givens={self.x: in_x},name='score',
			allow_input_downcast=True)#,on_unused_input='warn')
		return fn

	def __l1Regularization__(self,start=0):
		"""
		Do L1 Regularization
		train_objective = cross_entropy + self.l2_reg * [l1 norm of all weight matrices]
		"""
		#if self.l1_reg is not None:
		for i in xrange(start,self.n_layers):
			W = self.params[i * 2]
			self.finetune_cost += self.l1_reg * (abs(W).sum())

	def __l2Regularization__(self,start=0):
		"""
		l2 norm regularization weight
		train_objective = cross_entropy + self.l2_reg * [l2 norm of all weight matrices]
		"""
		#if self.l2_reg is not None:
		for i in xrange(start,self.n_layers):
			W = self.params[i * 2]
			self.finetune_cost += self.l2_reg * T.sqr(W).sum()

	def __TrainReg__(self,updates,start=0):
		"""
		l2 norm regularization weight
		"""
		#if self.max_col_norm is not None:
		for i in xrange(start,self.n_layers):
			W = self.params[i * 2]
			if W in updates:
				updated_W = updates[W]
				col_norms = T.sqrt(T.sum(T.sqr(updated_W), axis=0))
				desired_norms = T.clip(col_norms, 0, self.max_col_norm)
				updates[W] = updated_W * (desired_norms / (1e-7 + col_norms))
		return updates

	def save(self,filename,start_layer = 0,max_layer_num = -1,withfinal=True):
		nnet_dict = {}
		if max_layer_num == -1:
		   max_layer_num = self.n_layers

		for i in range(start_layer, max_layer_num):
			dict_a = str(i) + ' W'
			nnet_dict[dict_a] = _array2string(self.layers[i].params[0].get_value())
			dict_a = str(i) + ' b'
			nnet_dict[dict_a] = _array2string(self.layers[i].params[1].get_value())

		if withfinal: 
			dict_a = 'logreg W'
			nnet_dict[dict_a] = _array2string(self.logLayer.params[0].get_value())
			dict_a = 'logreg b'
			nnet_dict[dict_a] = _array2string(self.logLayer.params[1].get_value())

		with open(filename, 'wb') as fp:
			json.dump(nnet_dict, fp, indent=2, sort_keys = True)
			fp.flush()

	def load(self,filename,start_layer = 0,max_layer_num = -1,withfinal=True):
		nnet_dict = {}
		if max_layer_num == -1:
			max_layer_num = self.n_layers

		with open(filename, 'rb') as fp:
			nnet_dict = json.load(fp)
		
		for i in xrange(max_layer_num):
			dict_key = str(i) + ' W'
			self.layers[i].params[0].set_value(numpy.asarray(_string2array(nnet_dict[dict_key]),
				dtype=theano.config.floatX))
			dict_key = str(i) + ' b' 
			self.layers[i].params[1].set_value(numpy.asarray(_string2array(nnet_dict[dict_key]),
				dtype=theano.config.floatX))

		if withfinal:
			dict_key = 'logreg W'
			self.logLayer.params[0].set_value(numpy.asarray(_string2array(nnet_dict[dict_key]),
				dtype=theano.config.floatX))
			dict_key = 'logreg b'
			self.logLayer.params[1].set_value(numpy.asarray(_string2array(nnet_dict[dict_key]),
				dtype=theano.config.floatX))

# convert an array to a string
def _array2string(array):
	str_out = StringIO()
	numpy.savetxt(str_out, array)
	return str_out.getvalue()

# convert a string to an array
def _string2array(string):
	str_in = StringIO(string)
	return numpy.loadtxt(str_in)

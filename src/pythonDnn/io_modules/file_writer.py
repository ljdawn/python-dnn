
import json,numpy,os
from pythonDnn.io_modules import create_folder_structure_if_not_exists

import logging
logger = logging.getLogger(__name__)
	
def write_dataset(options):
	file_path = options['base_path'] + os.sep + options['filename'];
	logger.info("%s dataset will be initialized to write to %s",
				options['writer_type'],file_path);
	create_folder_structure_if_not_exists(file_path);
	file_writer = FileWriter.get_instance(file_path,options);
	file_writer.write_file_info()
	return file_writer

##########################################BASE CLASS##############################################################

class FileWriter(object):
	header = None
	feat_dim = None
	filepath = None
	filehandle = None
	
	@staticmethod
	def get_instance(path,header):
		if(header['writer_type']=='T1'):
			return T1FileWriter(path,header);
		elif header['writer_type']=='TD':
			return TDFileWriter(path,header);
		elif header['writer_type']=='NP':
			return NPFileWriter(path,header);
		else:
			logger.critical("`%s` writer_type is not defined...",options['writer_type'])
			
	def __init__(self,filepath,header):
		self.header = header
		self.filepath = filepath
		self.feat_dim = header['featdim'];
		self.filehandle = open(self.filepath,'ab')
		
	def write_file_info(self):
		pass
	def write_data(self,vector_array,labels):
		pass
		
##########################################NP Filewriter##############################################################
"""
	writes the dataset which is stored as single file in binary format
	<json-header>
	<feat_vector>	> stored as structured numpy.array
	.
	.
"""

class NPFileWriter(FileWriter):
	def __init__(self,filepath,header):
			super(NPFileWriter,self).__init__(filepath,header)

	def write_file_info(self):
		self.filehandle.write(json.dumps(self.header)+'\n')
		dt={'names': ['d','l'],'formats': [('>f2',self.feat_dim),'>i2']}
		logger.debug('NP Filewriter : feats : %s' % str(dt))

	def write_data(self,vector_array,labels):
		dt={'names': ['d','l'],'formats': [('>f2',self.feat_dim),'>i2']}
		data = numpy.zeros(1,dtype= numpy.dtype(dt))
		for vector,label in zip(vector_array,labels):
			flatten_vector = vector.flatten();
			if self.feat_dim!=len(flatten_vector):
				logger.critical('Feature dimension mentioned in header and vector length are mismatching');
				exit(0)
			else:
				data['d']=flatten_vector; data['l']=label;
				data.tofile(self.filehandle); 
		self.filehandle.flush();
		logger.debug('NP Filewriter : data writen to %s' % self.filepath)
##########################################TD FILEREADER##############################################################
"""
	Reads the simple text file following is the structure
	<feat_dim> <num_feat_vectors>(optional)
	<feat_vector>
	<feat_vector>
	.
	.
"""
class TDFileWriter(FileWriter):
	def __init__(self,filepath,header):
		super(TDFileWriter,self).__init__(filepath,header)

	def write_file_info(self):
		self.filehandle.write(str(self.feat_dim)+os.linesep)
		logger.debug('TD Filewriter : feats : %d' % self.feat_dim)

	def write_data(self,vector_array,labels):
                
		#for vector,label in zip(vector_array,labels):
		#	flatten_vector = vector.flatten();
		#	if self.feat_dim!=len(flatten_vector):
		#		logger.critical('Feature dimension mentioned in header and vector length are mismatching');
		#		exit(0)
		#	else:
		#		for element in vector:
		#			self.filehandle.write('%f ' % element)
		#	self.filehandle.write(os.linesep);
		(n,m)=vector_array.shape;
                if self.feat_dim!=m:
                        logger.critical('Feature dimension mentioned in header and vector length are mismatching');
                        exit(0)
                numpy.savetxt(self.filehandle,vector_array, fmt='%f', delimiter=' ');
                self.filehandle.flush();		
		logger.debug('TD Filewriter : data writen to %s [%d]',self.filepath,n)

"""
class T1FileWriter(FileWriter):
	def __init__(self,path,header):
		self.header = header
		self.filepath = path
		self.filehandle = open(self.filepath,'a+')
		self.childhandles = []

	def write_file_info(self):
		self.filehandle.write(('%d %d'+os.linesep) % (self.header['featdim'],self.header['classes']))
		self.path = self.header['path'];
		
		for idx in xrange(0,self.classes):
			child_header = self.header.copy();
			child_header['filename'] = "%d.data"%label
			path = child_header['base_path'] + os.sep + child_header['filename'] 
			filehandle.write(path + os.linesep);
			self.childhandles.append(TDFileWriter(path,child_header));
			self.childhandles[-1].write_file_info();
		self.filehandle.flush()
		
	def write_data(self,vectors,labels):
		featdim = self.header[0];
		for vector,label in zip(vectors,labels):
			flatten_vector = vector.flatten();
			if featdim==len(flatten_vector):
				logger.critical('Feature dimension mentioned in header and vector length is mismatching');
				self.childhandles[label].writedata(vector,label); 

"""

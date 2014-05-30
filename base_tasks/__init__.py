# import os,inspect

# def _istask(obj):
# 	return hasattr(obj,'taskname')

# importdict = {}
# taskdir,modname = os.path.split(__file__)

# for fullname in os.listdir(taskdir):
# 	fname,ext = os.path.splitext(fullname)

# 	if (not fname.startswith('_')) and (ext.lower() == '.py'):

# 		submodname = '.'.join([taskdir,fname])
# 		mod = __import__(submodname,globals(),locals(),['*'],-1)

# 		loadnames = []
# 		for name,obj in inspect.getmembers(mod,predicate=_istask):
# 			if obj.taskname in loadnames:
# 				print 'Ignoring duplicate of task "%s" in %s' %(obj.taskname,fullname)
# 			else:
# 				loadnames.append(name)

# 		# if len(loadnames):
# 		# 	importdict.update({submodname:loadnames})

# 		del mod

# 	else: 
# # 		continue

# import pkgutil

# __all__ = []
# for loader, module_name, is_pkg in  pkgutil.walk_packages(__path__):
# 	__all__.append(module_name)
# 	module = loader.find_module(module_name).load_module(module_name)
# 	exec('%s = module' %module_name)
#!/usr/bin/env python

import os
import string
import glob
import shutil

from retengine import models
from retengine import utils
import base_caches

#
# Cache Inheritance Hierarchy:
#
#            ---------------
#           | SessionCache |
#           ---------------
#                :
#        -------[]-----------------
#       | SessionExcludeListCache |
#       --------------------------
#                 |
#                 v
#           ----------------
#          | CompDataCache |
#          ----------------

PATTERN_FNAME_ANNOFILE = '${query_strid}.txt'
POSTRAINIMGS_DIRNAME = 'postrainimgs'
CURATEDTRAINIMGS_DIRNAME = 'curatedtrainimgs'
UPLOADEDIMGS_DIRNAME = 'uploadedimgs'

class CompDataCache(base_caches.SessionExcludeListCache):
    """
        Cache for computational data in VISOR frontend (interfaces to disk cache)

        Most functions operate through a system of callbacks, with the following callbacks
        specifiable by adding to the callbacks property:

          save_classifier
          load_classifier
          save_annotations
          load_annotations_and_trs
          get_annotations

        These callbacks handle the actual reading/writing of computational data to the
        filenames returned by the '_get_classifier_fname' and '_get_annotations_fname'
        functions.

        There are also some utility functions for determining the paths of other
        stores of computational data (with reading/writing left to the user):

          get_training_images
          get_feature_dir
          convert_system_path_to_server_path
    """

    def __init__(self, compdata_paths, engines_dict, disable_cache=False,
                 callbacks=dict()):
        """
            Initializes the cache.
            Arguments:
                compdata_paths: Instance of CompDataPaths
                engines_dict: Dictionary of supported engines
                disable_cache: Boolean indicating whether or not the cache should be disable.
                callbacks: Dictionary of callback functions.
        """
        if not isinstance(compdata_paths, models.param_sets.CompDataPaths):
            raise ValueError('compdata_paths must be of type models.param_sets.CompDataPaths')
        self._compdata_paths = compdata_paths
        self.disable_cache = disable_cache
        self.callbacks = callbacks
        self.engines_dict = engines_dict

        super(CompDataCache, self).__init__()

    # ----------------------------------
    ## Classifier component
    # ----------------------------------

    def save_classifier(self, query, **kwargs):
        """
            Saves the classifier of the specified query to a local file,
            if the query is not excluded and the cache is enabled.
            Arguments:
                query: query in dictionary form.
                kwargs: Arguments for the 'save_classifier' callback, if available.
            Returns:
                The value returned by the 'save_classifier' callback, if available.
                'False' if the 'save_classifier' callback is not available.
                'None' if the query is excluded or the cache is enabled.
        """
        # pop user_ses_id from kwargs if it exists
        user_ses_id = kwargs.pop('user_ses_id', None)

        # determine if on cache exclude list
        excl_query = self.query_in_exclude_list(query, ses_id=user_ses_id)

        if not self.disable_cache and not excl_query:
            fname = self._get_classifier_fname(query)
            if 'save_classifier' in self.callbacks:
                return self.callbacks['save_classifier'](query, fname, **kwargs)
            else:
                return False


    def load_classifier(self, query, **kwargs):
        """
            Loads the classifier of the specified query from a local file,
            if the query is not excluded and the cache is enabled.
            Arguments:
                query: query in dictionary form.
                kwargs: Arguments for the 'load_classifier' callback, if available.
            Returns:
                The value returned by the 'load_classifier' callback, if available.
                'False' if the 'load_classifier' callback is not available.
                'None' if the query is excluded or the cache is enabled.
        """
        # pop user_ses_id from kwargs if it exists
        user_ses_id = kwargs.pop('user_ses_id', None)

        # determine if on cache exclude list
        excl_query = self.query_in_exclude_list(query, ses_id=user_ses_id)

        #print '*******************************'
        #print 'user_ses_id: %s' % user_ses_id
        #print 'query: %s' % query
        #print 'caching disabled: %s' % self.disable_cache
        #print 'query on exclude list: %s' % excl_query
        #print '*******************************'

        if not self.disable_cache and not excl_query:
            fname = self._get_classifier_fname(query)
            if 'load_classifier' in self.callbacks:
                return self.callbacks['load_classifier'](query, fname, **kwargs)
            else:
                return False


    def _get_classifier_fname(self, query):
        """
            Gets the full path and filename of the classifier associated to the
            specified query.
            Arguments:
                query: query in dictionary form.
            Returns:
                A file path where the file name follows the configured
                'pattern_fname_classifier'.
        """
        query_strid = utils.tag_utils.get_query_strid(query)

        classifiers_path = self._compdata_paths.classifiers
        engine = query['engine']
        classifiers_path = os.path.join(classifiers_path, engine)

        fname_template = string.Template( self.engines_dict[ engine ]['pattern_fname_classifier'] )
        fname = fname_template.substitute(query_strid=query_strid)
        try:
            os.makedirs(classifiers_path)
        except OSError:
            pass

        return os.path.join(classifiers_path, fname)

    # ----------------------------------
    ## Annotation component
    # ----------------------------------

    def save_annotations(self, query, **kwargs):
        """
            Saves the annotations of the specified query to a local file,
            if the query is not excluded and the cache is enabled.
            Arguments:
                query: query in dictionary form.
                kwargs: Arguments for the 'save_annotations' callback, if available.
            Returns:
                The value returned by the 'save_annotations' callback, if available.
                'False' if the 'save_annotations' callback is not available.
                'None' if the query is excluded or the cache is enabled.
        """
        # pop user_ses_id from kwargs if it exists
        user_ses_id = kwargs.pop('user_ses_id', None)

        # determine if on cache exclude list
        excl_query = self.query_in_exclude_list(query, ses_id=user_ses_id)

        if not self.disable_cache and not excl_query:
            fname = self._get_annotations_fname(query)
            if 'save_annotations' in self.callbacks:
                return self.callbacks['save_annotations'](query, fname, **kwargs)
            else:
                return False


    def load_annotations_and_trs(self, query, **kwargs):
        """
            Loads the annotations of the specified query from a local file,
            if the query is not excluded and the cache is enabled.
            It should differ from 'get_annotations' in that this function
            should return a simple value indicating the success (or not) of the
            loading process.
            Arguments:
                query: query in dictionary form.
                kwargs: Arguments for the 'load_annotations_and_trs' callback, if available.
            Returns:
                The value returned by the 'load_annotations_and_trs' callback, if available.
                'False' if the 'load_annotations_and_trs' callback is not available.
                'None' if the query is excluded or the cache is enabled.
        """
        # pop user_ses_id from kwargs if it exists
        user_ses_id = kwargs.pop('user_ses_id', None)

        # determine if on cache exclude list
        excl_query = self.query_in_exclude_list(query, ses_id=user_ses_id)

        if not self.disable_cache and not excl_query:
            fname = self._get_annotations_fname(query)
            if 'load_annotations_and_trs' in self.callbacks:
                return self.callbacks['load_annotations_and_trs'](query, fname, **kwargs)
            else:
                return False


    def get_annotations(self, query, **kwargs):
        """
            Gets the annotations of the specified query from a local file,
            if the query is not excluded and the cache is enabled.
            It should differ from 'load_annotations_and_trs' in that this function
            should return a list of dictionaries with the actual annotations.
            Arguments:
                query: query in dictionary form.
                kwargs: Arguments for the 'get_annotations' callback, if available.
            Returns:
                The value returned by the 'get_annotations' callback, if available.
                'False' if the 'get_annotations' callback is not available.
                'None' if the query is excluded or the cache is enabled.
        """
        # pop user_ses_id from kwargs if it exists
        user_ses_id = kwargs.pop('user_ses_id', None)

        # determine if on cache exclude list
        excl_query = self.query_in_exclude_list(query, ses_id=user_ses_id)

        if not self.disable_cache and not excl_query:
            fname = self._get_annotations_fname(query)
            if 'get_annotations' in self.callbacks:
                return self.callbacks['get_annotations'](query, fname, **kwargs)
            else:
                return False


    def _get_annotations_fname(self, query):
        """
            Gets the full path and filename of the annotations associated to the
            specified query.
            Arguments:
                query: query in dictionary form.
            Returns:
                A file path where the file name follows PATTERN_FNAME_ANNOFILE.
        """
        query_strid = utils.tag_utils.get_query_strid(query)
        fname_template = string.Template(PATTERN_FNAME_ANNOFILE)
        fname = fname_template.substitute(query_strid=query_strid)

        postrainanno_path = self._compdata_paths.postrainanno
        engine = query['engine']
        postrainanno_path = os.path.join(postrainanno_path, engine)

        try:
            os.makedirs(postrainanno_path)
        except OSError:
            pass

        return os.path.join(postrainanno_path, fname)

    # ----------------------------------
    ## Manage all compdata components
    # ----------------------------------

    def delete_compdata(self, query):
        """
            Deletes all computational data associated to the specified
            query, i.e., the classifier, the annotations, any precomputed
            features and any downloaded training images.
            Arguments:
                query: query in dictionary form.
        """
        # delete classifier if it exists
        classif_fname = self._get_classifier_fname(query)
        anno_fname = self._get_annotations_fname(query)
        try:
            if 'save_classifier' in self.callbacks and os.path.exists(classif_fname):
                os.remove(classif_fname)
                print 'REMOVED FILE:', classif_fname
        except Exception as e:
            print e
            pass # avoid an exception here from preventing the execution of the code below

        try:
            if 'save_annotations' in self.callbacks and os.path.exists(anno_fname):
                os.remove(anno_fname)
                print 'REMOVED FILE:', anno_fname
        except Exception as e:
            print e
            pass # avoid an exception here from preventing the execution of the code below

        try:
            postrainimgs_path = self.get_image_dir(query)
            if (os.path.exists(postrainimgs_path)
                and postrainimgs_path!=os.path.join(self._compdata_paths.datasets, query['dsetname']) # avoid deleting the complete set of dataset images
                and self._compdata_paths.uploadedimgs!=postrainimgs_path    # avoid deleting the complete uploadedimgs directory
                and self._compdata_paths.curatedtrainimgs not in postrainimgs_path):  # avoid deleting any curated training images
                shutil.rmtree(postrainimgs_path)
                print 'REMOVED FOLDER:', postrainimgs_path
        except Exception as e:
            print e
            pass # avoid an exception here from preventing the execution of the code below

        try:
            postrainfeats_path =  self.get_feature_dir(query)
            if os.path.exists(postrainfeats_path) and postrainfeats_path!=os.path.join(self._compdata_paths.postrainfeats, query['engine'] ):
                shutil.rmtree(postrainfeats_path)
                print 'REMOVED FOLDER:', postrainfeats_path
        except Exception as e:
            print e
            pass  # avoid an exception here from preventing the execution of the code below

        # ADD DELETION FOR OTHER COMPDATA COMPONENTS HERE AS THEY ARE ADDED...


    # ----------------------------------
    ## Clear caches
    # ----------------------------------

    def clear_features_cache(self):
        """  Clears up the directory of cached features for all configured engines """
        for engine in self.engines_dict:
            postrainfeats_path = os.path.join(self._compdata_paths.postrainfeats, engine )
            utils.fileutils.delete_directory_contents(postrainfeats_path)


    def clear_annotations_cache(self):
        """  Clears up the directory of cached annotations for all configured engines """
        for engine in self.engines_dict:
            postrainanno_path = os.path.join(self._compdata_paths.postrainanno, engine )
            utils.fileutils.delete_directory_contents(postrainanno_path)


    def clear_classifiers_cache(self):
        """  Clears up the directory of cached classifiers for all configured engines """
        for engine in self.engines_dict:
            classifiers_path = os.path.join(self._compdata_paths.classifiers, engine )
            utils.fileutils.delete_directory_contents(classifiers_path)


    def clear_postrainimgs_cache(self):
        """  Clears up the directory of downloaded positive training images for all configured engines """
        for engine in self.engines_dict:
            postrainimgs_path = os.path.join(self._compdata_paths.postrainimgs, engine )
            utils.fileutils.delete_directory_contents(postrainimgs_path)


    def cleanup_unused_query_postrainimgs_cache(self, query):
        """
            Clears up 'unused' positive training images for the specified
            query. Images become 'unused' if they are downloaded but not
            listed in the annotations file for the query.
            Arguments:
                query: query in dictionary form.
        """
        # For the specified query, remove the postrainimgs images
        # that are not listed in the annotation file
        annotations_file_name = self._get_annotations_fname(query)
        postrainimgs_files = []
        if os.path.isfile(annotations_file_name):
            with open(annotations_file_name) as annotations_file:
                for line in annotations_file:
                    path = line.split('\t')[0]
                    path = path.split(' ')[0]
                    if path.startswith(POSTRAINIMGS_DIRNAME):
                        path = path.replace( POSTRAINIMGS_DIRNAME, self._compdata_paths.postrainimgs)
                    postrainimgs_files.append(path)
            postrainimg_folder = self.get_image_dir(query)
            for the_file in os.listdir(postrainimg_folder):
                file_path = os.path.join(postrainimg_folder, the_file)
                try:
                    if (file_path not in postrainimgs_files) and os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception, e:
                    print e
                    pass

    # ----------------------------------
    ## Get paths and disk filenames
    # ----------------------------------

    def get_image_dir(self, query):
        """
            Gets the path to the folder where the images associated to a
            query are stored. The path varies not only depending on the
            query itself but also depending on the query type
            (see 'models.opts.qtypes'). This function also creates the
            folder if it did not exist.
            Arguments:
                query: query in dictionary form.
        """
        query_strid = utils.tag_utils.get_query_strid(query)

        if query['qtype'] == models.opts.qtypes.text:
            postrainimgs_path = self._compdata_paths.postrainimgs
            postrainimgs_path = os.path.join(postrainimgs_path, query['engine'] )
            rootdir = os.path.join(postrainimgs_path, query_strid)
            try:
                os.makedirs(rootdir)
                os.chmod(rootdir,0774)
            except OSError:
                pass
            return rootdir
        elif query['qtype'] == models.opts.qtypes.curated:
            curatedtrainimgs_path = self._compdata_paths.curatedtrainimgs
            curatedtrainimgs_path = os.path.join(curatedtrainimgs_path, query['engine'] )
            rootdir = os.path.join(curatedtrainimgs_path, query_strid)
            posdir = os.path.join(rootdir, 'positive')
            negdir = os.path.join(rootdir, 'negative')
            if not os.path.isdir(posdir) or not os.path.isdir(negdir):
                errmsg = 'Directory containing curated classifiers does not exist'
                raise models.errors.CuratedClassifierPathNotFoundError(errmsg)
            return rootdir
        elif query['qtype'] == models.opts.qtypes.image:
            rootdir = os.path.join(self._compdata_paths.uploadedimgs)
            try:
                os.makedirs(rootdir)
            except OSError:
                pass
            return rootdir
        elif query['qtype'] == models.opts.qtypes.refine:
            postrainimgs_path = os.path.join(self._compdata_paths.postrainimgs)
            # if there are curated images in the refined search. change the source folder
            if 'curated__' in str(query['qdef']):
                postrainimgs_path = os.path.join(self._compdata_paths.curatedtrainimgs)
            postrainimgs_path = os.path.join(postrainimgs_path, query['engine'] )
            try:
                os.makedirs(postrainimgs_path)
            except OSError:
                pass
            return postrainimgs_path
        elif query['qtype'] == models.opts.qtypes.dsetimage:
            rootdir = os.path.join(self._compdata_paths.datasets, query['dsetname'])
            try:
                os.makedirs(rootdir)
            except OSError:
                pass
            return rootdir
        else:
            raise models.errors.UnsupportedQtypeError('qtype not supported')


    def get_training_images(self, query, **kwargs):
        """
            Gets a list of dictionaries, where each dictionary contains the
            path to an image and its annotation indicating if it is a positive,
            negative or neutral training image.
            Arguments:
                query: query in dictionary form.
                kwargs: Arguments for the 'get_annotations' callback, if available.
        """
        # pop full_path from kwargs if it exists
        full_path = kwargs.pop('full_path', False)

        if query['qtype'] in [models.opts.qtypes.text, models.opts.qtypes.refine]:
            annos = self.get_annotations(query, **kwargs)
            if annos:
                for anno in annos:
                    if CURATEDTRAINIMGS_DIRNAME in anno['image']:
                        anno['image'] = self.convert_system_path_to_server_path(anno['image'],
                                                                        CURATEDTRAINIMGS_DIRNAME + os.sep)
                    else:
                        anno['image'] = self.convert_system_path_to_server_path(anno['image'],
                                                                        POSTRAINIMGS_DIRNAME + os.sep)
            return annos
        elif query['qtype'] == models.opts.qtypes.curated:
            imagedir = self.get_image_dir(query)
            imagedir = os.path.join(imagedir, 'positive')
            image_fns = glob.glob(os.path.join(imagedir, '*.jpg'))
            if not full_path:
                imagedirtop = os.path.basename(os.path.normpath(imagedir))
                return [os.path.join(imagedirtop, os.path.basename(image_fn))
                        for image_fn in image_fns]
            else:
                return [os.path.join(imagedir, os.path.basename(image_fn))
                        for image_fn in image_fns]
        elif query['qtype'] == models.opts.qtypes.image:
            annos = self.get_annotations(query, **kwargs)
            for anno in annos:
                anno['image'] = self.convert_system_path_to_server_path(anno['image'],
                                                                        UPLOADEDIMGS_DIRNAME + os.sep)
            return annos
        elif query['qtype'] == models.opts.qtypes.dsetimage:
            annos = self.get_annotations(query, **kwargs)
            for anno in annos:
                anno['image'] = self.convert_system_path_to_server_path(anno['image'],
                                                                        query['dsetname'] + os.sep)
            return annos
        else:
            raise models.errors.UnsupportedQtypeError('qtype not supported')


    def get_feature_dir(self, query):
        """
            Gets the path to the folder where the features associated to a
            query are stored. The path varies not only depending on the
            query itself but also depending on the query type
            (see 'models.opts.qtypes'). This function also creates the
            folder if it did not exist.
            Arguments:
                query: query in dictionary form.
        """
        query_strid = utils.tag_utils.get_query_strid(query)

        if query['qtype'] == models.opts.qtypes.text:
            postrainfeats_path = self._compdata_paths.postrainfeats
            postrainfeats_path = os.path.join(postrainfeats_path, query['engine'] )
            rootdir = os.path.join(postrainfeats_path, query_strid)
            try:
                os.makedirs(rootdir)
            except OSError:
                pass
            return rootdir
        elif query['qtype'] == models.opts.qtypes.refine:
            postrainfeats_path = os.path.join(self._compdata_paths.postrainfeats)
            postrainfeats_path = os.path.join(postrainfeats_path, query['engine'] )
            try:
                os.makedirs(postrainfeats_path)
            except OSError:
                pass
            return postrainfeats_path
        elif query['qtype'] == models.opts.qtypes.dsetimage:
            postrainfeats_path = os.path.join(self._compdata_paths.postrainfeats)
            postrainfeats_path = os.path.join(postrainfeats_path, query['engine'] )
            try:
                os.makedirs(postrainfeats_path)
            except OSError:
                pass
            return postrainfeats_path
        elif query['qtype'] == models.opts.qtypes.image:
            postrainfeats_path = os.path.join(self._compdata_paths.postrainfeats)
            postrainfeats_path = os.path.join(postrainfeats_path, query['engine'] )
            try:
                os.makedirs(postrainfeats_path)
            except OSError:
                pass
            return postrainfeats_path
        else:
            raise models.errors.UnsupportedQtypeError('qtype not supported')


    def convert_system_path_to_server_path(self, system_path, subdir):
        """
            Transforms a full system path into a relative path with respect
            to the specified sub-directory.
            Arguments:
                system_path: input system path
                subdir: sub-directory to remove from the system path
        """
        diridx = system_path.find(subdir)
        if diridx < 0:
            print 'WARNING: Could not parse path to positive training image path, check serverpath variable (system_path: %s, subdir: %s)' % (system_path, subdir)
            # return system_path, it could be it is already in the form we want it
            return system_path

        # extract the part we want
        system_path = system_path[diridx:]
        system_path = system_path.replace(subdir,'')
        system_path = system_path.replace(os.sep,'/')
        return system_path

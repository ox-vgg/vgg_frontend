#!/usr/bin/env python

import opts as retengine_opts

# ----------------------------------
## Parameter sets
# ----------------------------------

class VisorOptions(object):
    """ Class for storing the different parameters of the VISOR frontend interface """

    def __init__(self,
                 title='VISOR',
                 datasets={},
                 default_view=retengine_opts.Vmode.grid,
                 results_per_page=20,
                 engines={},
                 select_roi=False,
                 enable_viewsel=False,
                 check_backends_reachable=True,
                 disable_autocomplete=False):
        """
            Initializes the class
            Arguments:
                 title: Main page title
                 datasets: Dictionary of supported datasets
                 default_view: Default view mode
                 results_per_page: Number of items per results page
                 engines: Dictionary of supported engines
                 select_roi: Boolean indicating whether ROIs can be selected in the details page
                 enable_viewsel: Boolean indicating whether the view mode selector should be enable or not
                 check_backends_reachable: Boolean indicating whether the connection to the backend should be checked or not
                 disable_autocomplete: Boolean indicating whether autocomplete should be enable or not in the main query box
        """
        self.engines_dict = engines
        self.title = title
        self.datasets = datasets
        self.default_view = default_view
        self.results_per_page = results_per_page
        self.select_roi = select_roi
        self.enable_viewsel = enable_viewsel
        self.check_backends_reachable = check_backends_reachable
        self.disable_autocomplete = disable_autocomplete


class CompDataPaths(object):
    """ Class for storing the different paths for the computational data cache """

    # accept kwargs to drop unknown arguments
    def __init__(self, classifiers, postrainimgs,
                 uploadedimgs, curatedtrainimgs,
                 datasets, postrainanno,
                 postrainfeats, **kwargs):
        """
            Initializes the class
            Arguments:
                classifiers: Path to the classifiers files
                postrainimgs: Path to the positive training images
                uploadedimgs: Path to the files uploaded by the user
                curatedtrainimgs: Path to the images for curated training
                datasets: Path to the dataset files
                postrainanno: Path to the annotation files
                postrainfeats: Path to the features files
        """
        self.classifiers = classifiers
        self.postrainimgs = postrainimgs
        self.uploadedimgs = uploadedimgs
        self.curatedtrainimgs = curatedtrainimgs
        self.datasets = datasets
        self.postrainanno = postrainanno
        self.postrainfeats = postrainfeats


class MetaDataPaths(object):
    """ Class for storing the different paths for the metadata files """

    def __init__(self, metadata):
        """
            Initializes the class
            Arguments:
                metadata: Path to the JSON metadata files
        """
        self.metadata = metadata


class VisorEngineProcessOpts(object):
    """ Class for storing the different parameters to the VISOR engine interface """

    def __init__(self,
                 pool_workers=1,
                 resize_width=10000,
                 resize_height=10000,
                 disable_cache=False,
                 imsearchtools_opts=dict(service_host='localhost',
                                         service_port=35600,
                                         engine='google_web',
                                         query_timeout=3.0,
                                         improc_timeout=15.0,
                                         per_image_timeout=1.0,
                                         num_pos_train=200),
                 rf_rank_type=retengine_opts.RfRankTypes.full,
                 rf_rank_topn=2000,
                 rf_train_type=retengine_opts.RfTrainTypes.regular,
                 feat_detector_type=retengine_opts.FeatDetectorType.fast
                ):
        """
            Initializes the class
            Arguments:
                pool_workers: Number of feature computation workers
                resize_width: Maximum allowed width for a downloaded image
                resize_height:  Maximum allowed height for a downloaded image
                disable_cache: Boolean indicating whether the caches must be disable or not
                imsearchtools_opts: Dictionary of options for the image search tool
                    {   service_host: Address of host for the service
                        service_port: Port of service at host
                        engine: Name of default image downloader engine
                        query_timeout: Number of seconds for a query to timeout
                        improc_timeout: Number of seconds to timeout the processing of an image
                        per_image_timeout: Number of seconds for the download of an image to timeout
                        num_pos_train: Number of positive image to download
                    }
                rf_rank_type: Relevance feedback rank type
                rf_rank_topn: Relevance feedback rank type - Top N
                rf_train_type: Relevance feedback train type
                feat_detector_type: feature detector type to be used in the backend
        """
        self.pool_workers = pool_workers
        self.resize_width = resize_width
        self.resize_height = resize_height
        self.disable_cache = disable_cache
        self.imsearchtools_opts = imsearchtools_opts
        self.rf_rank_type = rf_rank_type
        self.rf_rank_topn = rf_rank_topn
        self.rf_train_type = rf_train_type
        self.feat_detector_type = feat_detector_type

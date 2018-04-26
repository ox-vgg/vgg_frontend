#  The line below requires msgpack-python==0.3.0 (if not already installed).
#  Install it by running: 'pip install msgpack-python==0.3.0'
import msgpack

query_text = 'name-of-predefined-list-of-results'
output_file_name = 'mydataset___text__{%s}.msgpack' % query_text
results_list = []
# This is the pattern: results_list.append( {'path': 'path-relative-to-image-data-folder' ,'roi': 'x1_y1_x2_y1_x2_y2_x1_y2_x1_y1' } )
# (x1,y1) corresponds to the top-left corner of the ROI and (x2,y2) to the bottom-right corner.
#
# An EMPTY results list should look like: results_list.append( {'path': '' , 'roi': '' } )
#
# This is an example of a NON-EMPTY list:
results_list.append({'path': 'master_list/box21/dvd306_062.tif.jpg', 'roi': '195.01_183.58_297.24_183.58_297.24_285.81_195.01_285.81_195.01_183.58'})
with open(output_file_name, 'wb') as rfile:
    msgpack.dump(results_list, rfile)

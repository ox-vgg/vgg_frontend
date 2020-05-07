#!/usr/bin/env python

from retengine.models import opts

# ----------------------------------
## JSON Schema (for use with validictory)
# ----------------------------------

_qtypes = [item for item in opts.Qtypes.__dict__
           if item != opts.Qtypes.text and
           item[:2] != "__"]
_qtypes.append('imageurl')

_query_schema_text_props = {"qdef": {"type": "string"},
                            "qtype": {"type": "string", "enum": [opts.Qtypes.text]},
                            "dsetname": {"type": "string"},
                            "engine": {"type": "string"},
                            "prev_qsid": {"type": "string", "required": False}}

_query_schema_image_props = {"qdef": {"type": "array",
                                      "items": {"type": "object",
                                                "properties": {"image": {"type": "string"},
                                                               "extra_prms": {"type": "object",
                                                                              "required": False}
                                                              }
                                               }
                                     },
                             "qtype": {"type": "string", "enum": _qtypes},
                             "dsetname": {"type": "string"},
                             "engine": {"type": "string"},
                             "prev_qsid": {"type": "string", "required": False}}

_jsonrpc_out_schema_success_props = {"jsonrpc": {"type": "string", "pattern": "2.0"},
                                     "result": {"type": "any"},
                                     "id": {"type": [{"type": "integer"},
                                                     {"type": "string", "minLength": 1}]
                                           }
                                    }
_jsonrpc_out_schema_failure_props = {"jsonrpc": {"type": "string", "pattern": "2.0"},
                                     "error": {"type": "object",
                                               "properties": {"code": {"type": "integer"},
                                                              "message": {"type": "string"},
                                                              "data": {"type": "object",
                                                                       "required": False}
                                                             }
                                              },
                                     "id": {"type": [{"type": "integer"},
                                                     {"type": "string", "minLength": 1}]
                                           }
                                    }

# schema for query dictionaries ---

query_schema = {"type": [{"type": "object",
                          "properties": _query_schema_text_props},
                         {"type": "object",
                          "properties": _query_schema_image_props}
                        ]
               }

# schema for API function not covered by above ---

api_proc_query_schema = {"type": "object",
                         "properties": {"qsid": {"type": "string"},
                                        "startidx": {"type": "integer", "required": False},
                                        "endidx": {"type": "integer", "required": False}
                                       }
                        }

# schema for JSON-RPC requests ---

jsonrpc_schema = {"type": "object",
                  "properties": {"jsonrpc": {"type": "string", "pattern": "2.0"},
                                 "method": {"type": "string", "minLength": 1},
                                 "params": {"type": "object", "required": False},
                                 "id": {"type": [{"type": "integer"},
                                                 {"type": "string", "minLength": 1}]
                                       }
                                }
                 }

jsonrpc_out_schema = {"type": [{"type": "object",
                                "properties": _jsonrpc_out_schema_success_props},
                               {"type": "object",
                                "properties": _jsonrpc_out_schema_failure_props}]
                     }

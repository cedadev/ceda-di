from enum import Enum

#some globals.
Script_status = Enum("Script_status",
                     "STORE_DATASET_TO_FILE \
                      READ_AND_SCAN_DATASET \
                      READ_DATASET_FROM_FILE_AND_SCAN\
                      RUN_SCRIPT_IN_LOTUS \
                      RUN_SCRIPT_IN_LOCALHOST \
                      READ_AND_SCAN_DATASETS_SUB \
                      READ_AND_SCAN_DATASETS \
                      STAY_IDLE"
                    )
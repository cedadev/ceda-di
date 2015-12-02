import re

from ceda_fbs._dataset import _geospatial


class Hyperspectral(_geospatial):
    @staticmethod
    def get_instrument(fname):
        if fname.startswith("e"):
            return {"instrument": "Eagle"}
        elif fname.startswith("f"):
            return {"instrument": "Hawk"}
        return {}

    @staticmethod
    def get_flight_info(fname):
        patterns = [
            r"arsf(?P<flight_num>\d{3}.*)-",
            r"(e|h)(\d{3})(\S?)(?P<flight_num>(\d{2,3})(\S?)((\d\S)?))"
        ]

        for patt in patterns:
            match = re.search(patt, fname)
            if match:
                flight_info = {
                    "organisation": "arsf",
                    "flight_num": match.group("flight_num")
                }

                return flight_info

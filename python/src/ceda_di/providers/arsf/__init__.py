from ceda_di._dataset import _geospatial

class Hyperspectral(object):
    @staticmethod
    def get_instrument(fname):
        if fname.startswith("e"):
            return {"instrument": "Eagle"}
        elif fname.startswith("f"):
            return {"instrument": "Hawk"}
        return {}

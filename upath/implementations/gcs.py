from upath.universal_path import _FSSpecAccessor, UniversalPath
import os
import re

class _GCSAccessor(_FSSpecAccessor):
    def __init__(self, parsed_url, *args, **kwargs):
        super().__init__(parsed_url, *args, **kwargs)

    def _format_path(self, s):
        """
        netloc has already been set to project via `GCSPath._init`
        """
        s = os.path.join(self._url.netloc, s.lstrip("/"))
        return s


# project is not part of the path, but is part of the credentials
class GCSPath(UniversalPath):
    _default_accessor = _GCSAccessor

    def _init(self, *args, template=None, **kwargs):
        # ensure that the bucket is part of the netloc path
        # need to pass token into accessor
        if kwargs.get("bucket") and kwargs.get("_url"):
            bucket = kwargs.pop("bucket")
            kwargs["_url"] = kwargs["_url"]._replace(netloc=bucket)
        super()._init(*args, template=template, **kwargs)

    def _sub_path(self, name):
        """s3fs returns path as `{bucket}/<path>` with listdir
        and glob, so here we can add the netloc to the sub string
        so it gets subbed out as well
        """
        sp = self.path
        subed = re.sub(f"^{self._url.netloc}/({sp}|{sp[1:]})/?", "", name)
        return subed

    def joinpath(self, *args):
        if self._url.netloc:
            return super().joinpath(*args)
        # handles a bucket in the path
        else:
            path = args[0]
            if isinstance(path, list):
                args_list = list(*args)
            else:
                args_list = path.split(self._flavour.sep)
            bucket = args_list.pop(0)
            self._kwargs["bucket"] = bucket
            return super().joinpath(*tuple(args_list)) 

    def mkdir(self, *args, **kwargs):
        # unless this is a bucket, we cannot create an empty 
        # directory in gcs since its not an actual file system
        bucket = self._url.netloc
        # if the path only includes the bucket, the parts will be empty
        if not self._parts:
            self.fs.mkdir(bucket)

    def write_bytes(self, data):
        with self.fs.open(self, "wb") as f:
            f.write(data)

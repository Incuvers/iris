
from pprint import pformat
from typing import Any, Dict, Tuple


class CMOSConfig:

    def __init__(self, name: str, resolution: Tuple[int, int], framerate: str):
        self.name = name
        self.width = resolution[0]
        self.height = resolution[1]
        self.framerate = framerate

    def __repr__(self) -> str:
        return "CMOS Profile: {}".format(pformat(self.getattrs()))

    def getattrs(self) -> Dict[str, Any]:
        """
        Iteratively get all object properties and values

        :return: object attributes and values
        :rtype: Dict[str, Any]
        """
        attributes: Dict[str, Any] = {}
        for k, v in vars(self).items():
            attributes[k.split('__')[-1]] = v
        return attributes

    def setattrs(self, **kwargs) -> None:
        """
        Iteratively set object properties
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        self.__name = name

    @property
    def width(self) -> int:
        return self.__width

    @width.setter
    def width(self, width: int) -> None:
        self.__width = width

    @property
    def length(self) -> int:
        return self.__length

    @length.setter
    def length(self, length: int) -> None:
        self.__length = length

    @property
    def framerate(self) -> str:
        return self.__framerate

    @framerate.setter
    def framerate(self, framerate: str) -> None:
        self.__framerate = framerate

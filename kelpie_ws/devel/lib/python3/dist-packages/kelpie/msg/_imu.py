# This Python file uses the following encoding: utf-8
"""autogenerated by genpy from kelpie/imu.msg. Do not edit."""
import codecs
import sys
python3 = True if sys.hexversion > 0x03000000 else False
import genpy
import struct

import kelpie.msg

class imu(genpy.Message):
  _md5sum = "ce43921e7b399d3ef9d38833a187cc81"
  _type = "kelpie/imu"
  _has_header = False  # flag to mark the presence of a Header object
  _full_text = """att att
xyz_float32 acc
xyz_float32 gyro
xyz_float32 gbias
xyz_float32 grav

================================================================================
MSG: kelpie/att
float32 roll
float32 pitch
float32 yaw

================================================================================
MSG: kelpie/xyz_float32
float32 x
float32 y
float32 z
"""
  __slots__ = ['att','acc','gyro','gbias','grav']
  _slot_types = ['kelpie/att','kelpie/xyz_float32','kelpie/xyz_float32','kelpie/xyz_float32','kelpie/xyz_float32']

  def __init__(self, *args, **kwds):
    """
    Constructor. Any message fields that are implicitly/explicitly
    set to None will be assigned a default value. The recommend
    use is keyword arguments as this is more robust to future message
    changes.  You cannot mix in-order arguments and keyword arguments.

    The available fields are:
       att,acc,gyro,gbias,grav

    :param args: complete set of field values, in .msg order
    :param kwds: use keyword arguments corresponding to message field names
    to set specific fields.
    """
    if args or kwds:
      super(imu, self).__init__(*args, **kwds)
      # message fields cannot be None, assign default values for those that are
      if self.att is None:
        self.att = kelpie.msg.att()
      if self.acc is None:
        self.acc = kelpie.msg.xyz_float32()
      if self.gyro is None:
        self.gyro = kelpie.msg.xyz_float32()
      if self.gbias is None:
        self.gbias = kelpie.msg.xyz_float32()
      if self.grav is None:
        self.grav = kelpie.msg.xyz_float32()
    else:
      self.att = kelpie.msg.att()
      self.acc = kelpie.msg.xyz_float32()
      self.gyro = kelpie.msg.xyz_float32()
      self.gbias = kelpie.msg.xyz_float32()
      self.grav = kelpie.msg.xyz_float32()

  def _get_types(self):
    """
    internal API method
    """
    return self._slot_types

  def serialize(self, buff):
    """
    serialize message into buffer
    :param buff: buffer, ``StringIO``
    """
    try:
      _x = self
      buff.write(_get_struct_15f().pack(_x.att.roll, _x.att.pitch, _x.att.yaw, _x.acc.x, _x.acc.y, _x.acc.z, _x.gyro.x, _x.gyro.y, _x.gyro.z, _x.gbias.x, _x.gbias.y, _x.gbias.z, _x.grav.x, _x.grav.y, _x.grav.z))
    except struct.error as se: self._check_types(struct.error("%s: '%s' when writing '%s'" % (type(se), str(se), str(locals().get('_x', self)))))
    except TypeError as te: self._check_types(ValueError("%s: '%s' when writing '%s'" % (type(te), str(te), str(locals().get('_x', self)))))

  def deserialize(self, str):
    """
    unpack serialized message in str into this message instance
    :param str: byte array of serialized message, ``str``
    """
    if python3:
      codecs.lookup_error("rosmsg").msg_type = self._type
    try:
      if self.att is None:
        self.att = kelpie.msg.att()
      if self.acc is None:
        self.acc = kelpie.msg.xyz_float32()
      if self.gyro is None:
        self.gyro = kelpie.msg.xyz_float32()
      if self.gbias is None:
        self.gbias = kelpie.msg.xyz_float32()
      if self.grav is None:
        self.grav = kelpie.msg.xyz_float32()
      end = 0
      _x = self
      start = end
      end += 60
      (_x.att.roll, _x.att.pitch, _x.att.yaw, _x.acc.x, _x.acc.y, _x.acc.z, _x.gyro.x, _x.gyro.y, _x.gyro.z, _x.gbias.x, _x.gbias.y, _x.gbias.z, _x.grav.x, _x.grav.y, _x.grav.z,) = _get_struct_15f().unpack(str[start:end])
      return self
    except struct.error as e:
      raise genpy.DeserializationError(e)  # most likely buffer underfill


  def serialize_numpy(self, buff, numpy):
    """
    serialize message with numpy array types into buffer
    :param buff: buffer, ``StringIO``
    :param numpy: numpy python module
    """
    try:
      _x = self
      buff.write(_get_struct_15f().pack(_x.att.roll, _x.att.pitch, _x.att.yaw, _x.acc.x, _x.acc.y, _x.acc.z, _x.gyro.x, _x.gyro.y, _x.gyro.z, _x.gbias.x, _x.gbias.y, _x.gbias.z, _x.grav.x, _x.grav.y, _x.grav.z))
    except struct.error as se: self._check_types(struct.error("%s: '%s' when writing '%s'" % (type(se), str(se), str(locals().get('_x', self)))))
    except TypeError as te: self._check_types(ValueError("%s: '%s' when writing '%s'" % (type(te), str(te), str(locals().get('_x', self)))))

  def deserialize_numpy(self, str, numpy):
    """
    unpack serialized message in str into this message instance using numpy for array types
    :param str: byte array of serialized message, ``str``
    :param numpy: numpy python module
    """
    if python3:
      codecs.lookup_error("rosmsg").msg_type = self._type
    try:
      if self.att is None:
        self.att = kelpie.msg.att()
      if self.acc is None:
        self.acc = kelpie.msg.xyz_float32()
      if self.gyro is None:
        self.gyro = kelpie.msg.xyz_float32()
      if self.gbias is None:
        self.gbias = kelpie.msg.xyz_float32()
      if self.grav is None:
        self.grav = kelpie.msg.xyz_float32()
      end = 0
      _x = self
      start = end
      end += 60
      (_x.att.roll, _x.att.pitch, _x.att.yaw, _x.acc.x, _x.acc.y, _x.acc.z, _x.gyro.x, _x.gyro.y, _x.gyro.z, _x.gbias.x, _x.gbias.y, _x.gbias.z, _x.grav.x, _x.grav.y, _x.grav.z,) = _get_struct_15f().unpack(str[start:end])
      return self
    except struct.error as e:
      raise genpy.DeserializationError(e)  # most likely buffer underfill

_struct_I = genpy.struct_I
def _get_struct_I():
    global _struct_I
    return _struct_I
_struct_15f = None
def _get_struct_15f():
    global _struct_15f
    if _struct_15f is None:
        _struct_15f = struct.Struct("<15f")
    return _struct_15f

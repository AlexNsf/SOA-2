# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: server.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0cserver.proto\x1a\x1bgoogle/protobuf/empty.proto\";\n\x0fRegisterRequest\x12\x0c\n\x04host\x18\x01 \x01(\t\x12\x0c\n\x04port\x18\x02 \x01(\x05\x12\x0c\n\x04name\x18\x03 \x01(\t\" \n\x10RegisterResponse\x12\x0c\n\x04uuid\x18\x01 \x01(\t\"\x1c\n\x0cLeaveRequest\x12\x0c\n\x04uuid\x18\x01 \x01(\t\"^\n\x14PerformActionRequest\x12\x0c\n\x04uuid\x18\x01 \x01(\t\x12\x0e\n\x06\x61\x63tion\x18\x02 \x01(\t\x12\x18\n\x0btarget_name\x18\x03 \x01(\tH\x00\x88\x01\x01\x42\x0e\n\x0c_target_name2\xaf\x01\n\x06Server\x12\x31\n\x08Register\x12\x10.RegisterRequest\x1a\x11.RegisterResponse\"\x00\x12\x30\n\x05Leave\x12\r.LeaveRequest\x1a\x16.google.protobuf.Empty\"\x00\x12@\n\rPerformAction\x12\x15.PerformActionRequest\x1a\x16.google.protobuf.Empty\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'server_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _REGISTERREQUEST._serialized_start=45
  _REGISTERREQUEST._serialized_end=104
  _REGISTERRESPONSE._serialized_start=106
  _REGISTERRESPONSE._serialized_end=138
  _LEAVEREQUEST._serialized_start=140
  _LEAVEREQUEST._serialized_end=168
  _PERFORMACTIONREQUEST._serialized_start=170
  _PERFORMACTIONREQUEST._serialized_end=264
  _SERVER._serialized_start=267
  _SERVER._serialized_end=442
# @@protoc_insertion_point(module_scope)

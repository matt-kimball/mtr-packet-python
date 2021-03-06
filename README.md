# mtrpacket

### Asynchronous network probes for Python

`mtrpacket` is a Python 3 package for sending IPv4 and IPv6 network probes ('pings') asynchronously from Python programs.  Python's `asyncio` library provides the event loop and mechanism for incorporating `mtrpacket`'s network probes with other concurrent operations.

`mtrpacket` supports a variety of probe customization options. Time-to-live (TTL) may be explicitly used for `traceroute`-like functionality.  Probes can be sent using a variety of protocols:  ICMP, UDP, TCP and SCTP.  UDP, TCP and SCTP probes may be sent with specific source and destination ports.  Probes can be sent with a particular packet size and payload bit-pattern. On Linux, probes can be sent with a routing "mark".

`mtrpacket` works on Linux, MacOS, Windows (under Cygwin) and various Unix systems.  Requirements are Python 3.5 (or newer) and `mtr`  0.88 (or newer).   `mtr` is distributed with many Linux distributions -- you may have it installed already.  For other operating systems, see [the mtr Github repository](https://github.com/traviscross/mtr).

## Installation

To install mtrpacket, use the Python 3 version of pip:

`pip3 install mtrpacket`

## Getting started

The easiest way to get started with mtrpacket is to use `async with` to open an mtrpacket session, and then call probe on that session. This must be done in an `asyncio` coroutine.  `asyncio` manages the event loop.

```python
import asyncio
import mtrpacket

#  A simple coroutine which will start an mtrpacket session and
#  ping localhost
async def probe():
    async with mtrpacket.MtrPacket() as mtr:
        return await mtr.probe('localhost')

#  Use asyncio's event loop to start the coroutine and wait for the probe
loop = asyncio.get_event_loop()
try:
    result = loop.run_until_complete(probe())
finally:
    loop.close()

#  Print the probe result
print(result)
```

Keyword arguments may be used with `mtr.probe` to further customize the network probe.

```python
#  Send a probe to the HTTPS port of example.com and limit the probe
#  to four network hops
result = await mtr.probe(
    'example.com',
    ttl=4,
    protocol='tcp',
    port=443)
```

## Further Examples

Further examples of usage are available in [the mtrpacket GitHub repository](https://github.com/matt-kimball/mtr-packet-python/tree/master/examples)

## Compatibility Notes

mtr version 0.93 has a known issue where a probe cannot be created without specifying a local IP address.  This will result in 'invalid-argument' results from sent probes.  You can work around this issue by specifying a local ip address when sending a probe:

```python
import socket

local_addr = socket.gethostbyname(socket.gethostname())
result = await mtr.probe('example.com', local_ip=local_addr)
```

## API Reference

### MtrPacket
#### *class* `MtrPacket()`

`MtrPacket` is a channel for communicating with a subprocess running the `mtr-packet` executable.  Multiple simultaneous probe requests can be made through a single `MtrPacket` instance, with results processed asynchronously, as they arrive.

The `mtr-packet` executable is distributed with versions of `mtr` since version 0.88.

#### *coroutine* `MtrPacket.open()`

`open` start a subprocess for sending and receiving network probes.  The`'mtr-packet` executable found at a location in the environment `PATH` is used by default, however, the environment variable `MTR_PACKET` can be used to override this behavior, invoking an alternate subprocess executable.

Rather than calling `open` explicitly, the usual alternative is to use an `MtrPacket` instance in an `async with` block.  This will launch the subprocess for the duration of the block, and terminate the subprocess when the block is exited.

`open` returns the `MtrPacket` object on which `open` has been invoked.  This can be safely ignored.

`ProcessError` is raised if the subprocess fails to execute, or if the subprocess executable doesn't support the expected interface.

`StateError` is raised if the `MtrPacket` object is already open.

#### *coroutine* `MtrPacket.close()`

If `open` was explicitly called to start the subprocess, then `close` should be called to terminate the subprocess and clean up its resources.

#### *coroutine* `MtrPacket.check_support(`*feature_name*`)`

`check_support` can be used to check support for particular features in the `mtr-packet` subprocess.  A string is provided with the name of a feature to check, and `True` is returned if the feature is supported, `False` otherwise.

The strings `'udp'`, `'tcp'` and `'sctp'` can be used as feature names to check support for UDP probes, TCP probes, and SCTP probes, respectively.

See `check-support` in the `mtr-packet(8)` man page for more information.

`ProcessError` is raised if the `mtr-packet` subprocess has unexpectedly terminated.

`StateError` is raised if the `MtrPacket` session hasn't been opened.

#### *coroutine* `MtrPacket.probe(`*hostname*, ...`)`

Send a network probe to a particular hostname or IP address, and upon completion, return a `ProbeResult` containing the status of the probe, the address of the host responding to the probe and the round trip time of the probe.

##### Keyword arguments

A number of optional keyword arguments can be used with `MtrPacket.probe`:

`ip_version`

Either `4` or `6`, indicating that the IP protocol version to use should be either IPv4 or IPv6.  If unspecified, the appropriate IP protocol version will be determined using the network configuration of the local host and the DNS resolved IP addresses.

`ttl`

An integer (0-255) for the "time to live" of the probe request.  This is used to limit the number of network hops the probe traverses before the probe result is returned to the origination point.  The default "time to live" for the probe is 255.

`protocol`

A string representing the protocol to use when sending the probe.  `'icmp'`, `'udp'`, `'tcp'` and `'sctp'` are recognized options.  Protocols other than `'icmp'` are not supported on all `mtr-packet` implementations.  If portability between `mtr-packet` implementations is desired, then`check_support` should be used to determine whether a particular protocol is supported before use.  The default protocol is `'icmp'`.

`port`

An integer to use as the destination port for `'udp'`, `'tcp'` or `'sctp'` probes.

`local_ip`

An IP address string used to set the source address of the probe to be a particular IP address.  This can be useful when sending from a host with multiple local IP addresses.  The default local address is determined using the network configuration.

`local_port`

An integer to use to send the probe from a particular local port, when sending `'udp'`, `'tcp'` or `'sctp'` probes.

`timeout`

An integer specifying the number of seconds to wait for a response before assuming the probe has been lost.  The default value is ten seconds.

`size`

An integer specifying the size of the generated probe packet, in bytes.  The default value is the minimum size possible for a packet of the particular IP version and protocol in use.  The maximum size is the maximum transmission unit ("MTU") of the local network configuration.

`bit_pattern`

An integer byte value used to fill the payload of the probe packet.  In some very rare cases, network performance can vary based on the contents of network packets.  This option can be used to measure such cases.

`tos`

An integer value for the "type of service" field for IPv4 packets, or the "traffic class" field of IPv6 packets.

`mark`

An integer value to use as the packet "mark" for the Linux routing subsystem.

##### Exceptions

`ProcessError` is raised if the mtr-packet subprocess has unexpectedly terminated.

`HostResolveError` is raised if the hostname can't be resolved to an IP address.

`StateError` is raised if the MtrPacket session hasn't been opened.

#### `MtrPacket.clear_dns_cache()`

For performance reasons, when repeatedly probing a particular host, MtrPacket will only resolve the hostname one time, and will use the same IP address for subsequent probes to the same host.

`clear_dns_cache` can be used to clear that cache, forcing new resolution of hostnames to IP addresses for future probes.  This can be useful for scripts which are intended to run for an extended period of time.  (Hours or longer)

### ProbeResult
#### *namedtuple* `ProbeResult(`*success*, *result*, *time_ms*, *responder*, *mpls*`)`

A call to `MtrPacket.probe` will result in an instance of the named tuple `ProbeResult`, which contains the following fields:

#### `ProbeResult.success`

A boolean which is `True` only if the probe arrived at the target host.

#### `ProbeResult.result`

The command reply string from `mtr-packet`.  Common values are `'reply'` for a probe which arrives at the target host, `'ttl-expired'` for a probe which has its "time to live" counter reach zero before arriving at the target host, and `'no-reply'` for a probe which is unanswered before its timeout value.

See the `mtr-packet(8)` man page for error conditions which may result in other command reply strings.

#### `ProbeResult.time_ms`

A floating point value indicating the number of milliseconds the probe was in-transit, prior to receiving a result.  This value will be `None` in cases other than `'reply'` or `'ttl-expired'`.

#### `ProbeResult.responder`
 
 A string with the IP address of the host responding to the probe.  Will be `None` in cases other than `'reply'` or `'ttl-expired'`.

#### `ProbeResult.mpls`

A list of `Mpls` named tuples representing the MPLS label stack present in a `'ttl-expired'` response, when Multiprotocol Label Switching (MPLS) is used to route the probe.

### Mpls
#### *namedtuple* `Mpls(`*label*, *traffic_class*, *bottom_of_stack*, *ttl*`)`

Multiprotocol Label Switching ("MPLS") routes packets using explicit headers attach to the packet, rather than using the IP address for routing.  When a probe's time-to-live ("TTL") expires, and MPLS is used at the router where the expiration occurs, the MPLS headers attached to the packet may be returned with the TTL expiration notification.

The `Mpls` named tuple contains the fields of one of those headers, with:

#### `Mpls.label`

The MPLS label as an integer.

#### `Mpls.traffic_class`

The integer traffic class value (for quality of service).  In prior verisons of MPLS, this field was known as "experimental use".

#### `Mpls.bottom_of_stack`

A boolean indicating whether the label terminates the stack.

#### `Mpls.ttl`

An integer with the "time to live" value of the MPLS header

### Exceptions
#### *exception* `StateError`

StateError is raised when attempting to send a command to the mtr-packet subprocess without first opening the MtrPacket subprocess, or when attempting to open a subprocess which is already open.

#### *exception* `HostResolveError`

If a hostname is passed to MtrPacket.probe, and that hostname fails to resolve to an IP address, `HostResolveError` is raised.

#### *exception* `ProcessError`

ProcessError is raised by a call to `MtrPacket.probe` or `MtrPacket.check_support` when the `mtr-packet` subprocess has unexpectly terminated.  It is also raised by `MtrPacket.open` when the subprocess doesn't respond using the expected `mtr-packet` interface.

# mtrpacket
Asynchronous network probes for Python

mtrpacket is a package for sending IPv4 and IPv6 network probes ('pings')
asynchronously from Python programs.  Python's asyncio library
provides the event loop and mechanism for incorporating mtrpacket's
network probes with other concurrent operations.

mtrpacket supports a variety of probe customization options.
Time-to-live (TTL) may be explicitly used for traceroute-like
functionality.  Probes can be sent using a variety of protocols:
ICMP, UDP, TCP and SCTP.  UDP, TCP and SCTP probes may be sent
with specific source and destination ports.  Probes can be sent
with a particular packet size and payload bit-pattern.
On Linux, probes can be sent with a routing "mark".

mtrpacket works on Linux, MacOS, Windows (with Cygwin) and
various Unix systems.  Requirements are Python (>= 3.6) and
mtr (>= 0.88).  mtr is distributed with many Linux distributions --
you may have it installed already.  For other operating systems,
see https://github.com/traviscross/mtr

## Getting started

The easiest way to get started with mtrpacket is to use `async with`
to open an mtrpacket session, and then call probe on that session.
This must be done in an asyncio coroutine.  asyncio manages the event loop.

For example:

```
import asyncio
import mtrpacket

#  A simple coroutine which will start an mtrpacket session and
#  ping localhost
async def probe():
    async with mtrpacket.MtrPacket() as mtr:
        return await mtr.probe('localhost')

#  Use asyncio's event loop to start the coroutine and wait for the probe
loop = asyncio.get_event_loop()
result = loop.run_until_complete(probe())

#  Print the probe result
print(result)
```

Keyword arguments may be used with `mtr.probe` to further customize
the network probe.  For example:

```
#  Send a probe to the HTTPS port of example.com and limit the probe
#  to four network hops
result = await mtr.probe(
    'example.com',
    ttl=4,
    protocol='tcp',
    port=443)
```

## MtrPacket
```python
MtrPacket(self)
```
The mtr-packet subprocess which can send network probes

MtrPacket opens a subprocess to an external 'mtr-packet' program,
and request that the subprocess send network probes.  Multiple
probe requests can be simultaneously in-transit, with results
processed asynchronously, as they arrive.

### open
```python
MtrPacket.open(self) -> 'MtrPacket'
```
Launch an mtr-packet subprocess to accept commands
(asynchronous)

Start a subprocess for accepting probe commands.  The 'mtr-packet'
executable in the PATH is used by default, however,
the MTR_PACKET environment variable can be used to specify
an alternate subprocess executable.

As an alternative to calling open() explicitly, an 'async with'
block can be used with the MtrPacket object to open and close the
subprocess.

Raises ProcessError if the subprocess fails to execute or
if the subprocess doesn't support sending packets.

Raises StateError if the subprocess is already open.

### close
```python
MtrPacket.close(self) -> None
```
Close an open mtr-packet subprocess
(asynchronous)

If open() was explicitly called to launch the mtr-packet
subprocess, close() should be used to terminate the process
and clean up resources.

### check_support
```python
MtrPacket.check_support(self, feature: str) -> bool
```
Check for support of a particular feature of mtr-packet
(asynchronous)

check_support() can be used to check support for particular
features in the mtr-packet subprocess.  For example, 'udp',
'tcp' and 'sctp' can be used to check support for UDP probes,
TCP probes, and SCTP probes.

See 'check-support' in the mtr-packet(8) man page for more
information.

Raises ProcessError if the mtr-packet subprocess has unexpectedly
terminated.

Raises StateError if the MtrPacket session hasn't been opened.

### probe
```python
MtrPacket.probe(self, host: str, **args) -> 'ProbeResult'
```
Asynchronously send a network probe
(asynchronous)

Send a network probe to a particular hostname or IP address,
returning a ProbeResult, which includes the status of the probe,
the address of the host responding to the probe and the round trip
time of the probe.

A number of optional keyword arguments can be used with the
probe request:


ip_version:
    Set the IP protocol version to either IPv4 or IPv6.

ttl:
    Set the "time to live" of the probe request.  This is used
    to limit the number of network hops the probe takes before
    the probe result is reported.

protocol:
    Can be 'icmp', 'udp', 'tcp' or 'sctp'.  A probe of the requested
    protocol is used.

port:
    The destination port to use for 'udp', 'tcp' or 'sctp' probes.

local_ip:
    Set the source address of the probe to a particular
    IP address.  Useful when sending from a host with multiple
    IP local addresses.

local_port:
    Send the probe from a particular port, when sending 'udp',
    'tcp' or 'sctp' probes.

timeout:
    The number of seconds to wait for a response before assuming
    the probe has been lost.

size:
    The size of the generated probe packet, in bytes.

bit_pattern:
    A byte value used to fill the payload of the probe packet.

tos:
    The value to use in the "type of service" field for IPv4
    packets, or the "traffic class" field of IPv6 packets.

mark:
    The packet "mark" value to be used by the Linux routing
    subsystem.


Raises ProcessError if the mtr-packet subprocess has unexpectedly
terminated.

Raises HostResolveError if the hostname can't be resolved to
an IP address.

Raises StateError if the MtrPacket session hasn't been opened.

## ProbeResult
```python
ProbeResult(self, /, *args, **kwargs)
```
A named tuple describing the result of a network probe

A call to MtrPacket.probe will result in an instance of
ProbeResult with the following members:

success:
    a bool which is True only if the probe arrived at the target
    host.

result:
    the command reply string from mtr-packet.  Common values
    are 'reply' for a probe which arrives at the target host,
    'ttl-expired' for a probe which has its "time to live"
    counter reach zero before arriving at the target host,
    and 'no-reply' for a probe which is unanswered.

    See the mtr-packet(8) man page for further command reply
    strings.

time_ms:
    a floating point value indicating the number of milliseconds
    the probe was in-transit, prior to receiving a result.
    Will be None in cases other than 'reply' or 'ttl-expired'.

responder:
    a string with the IP address of the host responding to the
    probe.  Will be None in cases other than 'reply' or 'ttl-expired'.

mpls:
    a list of Mpls tuples representing the MPLS label stack present in
    a 'ttl-expired' response, when Multiprotocol Label Switching (MPLS)
    is used to route the probe.

### mpls
Alias for field number 4
### responder
Alias for field number 3
### result
Alias for field number 1
### success
Alias for field number 0
### time_ms
Alias for field number 2
## Mpls
```python
Mpls(self, /, *args, **kwargs)
```
A named tuple describing an MPLS header.

Multiprotocol Label Switching (MPLS) routes packet using explicit
headers attach to the packet, rather than using the IP address
for routing.  When a probe's time-to-live (TTL) expires, and MPLS is
used at the router where the expiration occurs, the MPLS headers
attached to the packet may be returned with the TTL expiration
notification.

Mpls contains one of those headers, with:

label:
    the numeric MPLS label.

traffic_class:
    the traffic class (for quality of service).
    This field was formerly known as "experimental use".

bottom_of_stack:
    a boolean indicating whether the label terminates the stack.

ttl:
    the time-to-live of the MPLS header

### bottom_of_stack
Alias for field number 2
### label
Alias for field number 0
### traffic_class
Alias for field number 1
### ttl
Alias for field number 3
## StateError
```python
StateError(self, /, *args, **kwargs)
```
Exception raised when attempting to use MtrPacket in an invalid state

StateError is raised when attempting to send a command to the mtr-packet
subprocess without first opening the MtrPacket subprocess, or when
attempting to open a subprocess which is already open.

## HostResolveError
```python
HostResolveError(self, /, *args, **kwargs)
```
Exception raised when attempting to probe a non-resolving hostname

If a hostname is passed to MtrPacket.probe, and that hostname fails
to resolve to an IP address, HostResolveError is raised.

## ProcessError
```python
ProcessError(self, /, *args, **kwargs)
```
Exception raised when the mtr-packet subprocess unexpectedly exits

ProcessError is raised by a call to MtrPacket.probe
or MtrPacket.check_support when the mtr-packet subprocess has
unexpectly terminated.  It is also raised by MtrPacket.open when
the subprocess doesn't support the mtr-packet interface.


"""SOAP client for RCCService (Roblox Cloud Compute).

RCCService.exe is Roblox's binary — this only talks to a copy you run.
Default SOAP port is often 64989. Set rcc_soap in config.json.
"""
import uuid
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET


NS = {
    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
    "rbx": "http://roblox.com/",
}


def _envelope(body_inner: str) -> bytes:
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    {body_inner}
  </soap:Body>
</soap:Envelope>"""
    return xml.encode("utf-8")


def soap_call(url: str, action: str, body_inner: str, timeout: int = 15) -> str:
    data = _envelope(body_inner)
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f"http://roblox.com/{action}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def hello(url: str, timeout: int = 5) -> bool:
    try:
        soap_call(url, "HelloWorld", "<HelloWorld xmlns=\"http://roblox.com/\" />", timeout)
        return True
    except Exception:
        return False


def open_job(url: str, script_name: str, lua: str, expiration=120, timeout=15) -> str:
    job_id = str(uuid.uuid4())
    # escape lua for XML
    lua_xml = (
        lua.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    body = f"""
    <OpenJobEx xmlns="http://roblox.com/">
      <job>
        <id>{job_id}</id>
        <expirationInSeconds>{int(expiration)}</expirationInSeconds>
        <category>0</category>
        <cores>1</cores>
      </job>
      <script>
        <name>{script_name}</name>
        <script><![CDATA[{lua}]]></script>
      </script>
    </OpenJobEx>"""
    soap_call(url, "OpenJobEx", body, timeout)
    return job_id


def close_job(url: str, job_id: str, timeout: int = 10) -> None:
    body = f'<CloseJob xmlns="http://roblox.com/"><jobID>{job_id}</jobID></CloseJob>'
    try:
        soap_call(url, "CloseJob", body, timeout)
    except Exception:
        pass


def get_all_jobs(url: str, timeout: int = 10) -> str:
    return soap_call(url, "GetAllJobsEx", '<GetAllJobsEx xmlns="http://roblox.com/" />', timeout)

## To roll your own milter, create a class that extends Milter.
#  See the pymilter project at https://pythonhosted.org/pymilter/index.html

import logging
import os
import sys
from io import StringIO

import Milter
import redis
from Milter.utils import parse_addr

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("milter")


class myMilter(Milter.Base):

    def __init__(self):  # A new instance with each new connection.
        self.id = Milter.uniqueID()  # Integer incremented with each call.

    # each connection runs in its own thread and has its own myMilter
    # instance.  Python code must be thread safe.  This is trivial if only stuff
    # in myMilter instances is referenced.
    @Milter.noreply
    def connect(self, IPname, family, hostaddr):
        self.redis = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)
        return Milter.CONTINUE

    ##  def envfrom(self,f,*str):
    def envfrom(self, mailfrom, *str):
        self.mailfrom = mailfrom
        self.recipients = []  # list of recipients
        user, domain = parse_addr(mailfrom)
        self.canon_from = f"{user}@{domain}"
        return Milter.CONTINUE

    ##  def envrcpt(self, to, *str):
    @Milter.noreply
    def envrcpt(self, to, *str):
        self.recipients.append(to)
        return Milter.CONTINUE

    def eom(self):
        logger.info(f"EOM {self.canon_from} -> {self.recipients}")
        for recipient in self.recipients:
            canon_recipient = "@".join(parse_addr(recipient.lower()))
            if self.redis.sismember("blocked_emails", canon_recipient):
                self.delrcpt(recipient)
                logger.info(f"Blocked recipient: {recipient}")

        return Milter.ACCEPT

    def close(self):
        # always called, even when abort is called.  Clean up
        # any external resources here.
        return Milter.CONTINUE

    def abort(self):
        # client disconnected prematurely
        return Milter.CONTINUE


def main():
    socketname = "inet:9000@0.0.0.0"
    timeout = 600

    # Register to have the Milter factory create instances of your class:
    Milter.factory = myMilter
    flags = Milter.DELRCPT
    Milter.set_flags(flags)  # tell Sendmail which features we use
    # Milter.setdbg(3)
    Milter.settimeout(10)
    Milter.set_exception_policy(Milter.CONTINUE)
    logger.info("Milter startup")
    sys.stdout.flush()
    Milter.runmilter("pythonfilter", socketname, timeout)
    logger.info("Milter shutdown")


if __name__ == "__main__":
    main()

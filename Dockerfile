FROM --platform=${BUILDPLATFORM} alpine as tini-binary
ENV TINI_VERSION=v0.19.0
# Use BuildKit to help translate architecture names
ARG TARGETPLATFORM
# translating Docker's TARGETPLATFORM into tini download names
RUN case ${TARGETPLATFORM} in \
    "linux/amd64")  TINI_ARCH=amd64  ;; \
    "linux/arm64")  TINI_ARCH=arm64  ;; \
    "linux/arm/v7") TINI_ARCH=armhf  ;; \
    "linux/arm/v6") TINI_ARCH=armel  ;; \
    "linux/386")    TINI_ARCH=i386   ;; \
    esac \
    && wget -q https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-static-${TINI_ARCH} -O /tini \
    && chmod +x /tini

FROM python:3.11-slim

RUN pip install -U \
    pip \
    setuptools \
    wheel

WORKDIR /project

RUN useradd -m -r user && chown user /project

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

USER user

COPY --from=tini-binary /tini /tini
ENTRYPOINT ["/tini", "--"]

CMD ["python", "-m", "milter", "--bind-host", "0.0.0.0", "--bind-port", "9000"]

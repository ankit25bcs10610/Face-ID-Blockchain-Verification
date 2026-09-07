# ORYNEX AI API — FastAPI + InsightFace + ONNX Runtime
#
# The face pipeline pulls in a native CV/ML stack, so the image is built rather
# than run on a managed language runtime: the system libraries OpenCV links
# against and the buffalo_l model pack are both resolved here, at build time.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# libgl1 and libglib2.0-0 are the shared objects opencv-python links against;
# build-essential is needed because insightface compiles native extensions.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# numpy and Cython have to be importable before insightface builds its
# extensions, so they are installed ahead of the rest of the requirements.
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install numpy==2.4.6 "Cython>=3.0" \
    && pip install -r requirements.txt

# Bake the ~300 MB buffalo_l pack into the image. Downloading it lazily would
# make the first request after every deploy pay for it, on a filesystem that is
# thrown away on the next restart.
RUN python -c "from insightface.utils import storage; storage.ensure_available('models', 'buffalo_l')"

COPY . .

# EVIDENCE_DIR and the search caches resolve under /app/data, which is where the
# persistent disk is mounted in render.yaml.
ENV API_HOST=0.0.0.0 \
    PORT=10000

EXPOSE 10000

CMD ["sh", "-c", "exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-10000}"]

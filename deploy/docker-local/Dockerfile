FROM brewhouse-manager:dev as python-build

USER 0

COPY requirements.txt .

RUN pip install -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY scripts/seed-db.py /brewhouse-manager/api

WORKDIR /brewhouse-manager/api

ENTRYPOINT []

CMD poetry run python3 seed-db.py

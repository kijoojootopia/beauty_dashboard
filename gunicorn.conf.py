# Keep static assets responsive while the customs API fills its country cache.
# One process also shares the existing cache locks between HTTP requests.
workers = 1
worker_class = "gthread"
threads = 8

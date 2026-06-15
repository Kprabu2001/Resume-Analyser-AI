import logging

from app.base.log_context import get_request_id


class RequestIdFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        request_id = get_request_id()
        if request_id:
            short_id = request_id[-12:] if len(request_id) > 12 else request_id
            record.msg = f"[{short_id}] {record.msg}"
        return super().format(record)

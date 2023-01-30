from connect.eaas.core.enums import ResultType


class _Response:
    def __init__(self, status, output=None):
        self.status = status
        self.output = output

    @classmethod
    def done(cls, *args, **kwargs):
        """
        Create a new response as the task has been
        successfully processed.
        """
        return cls(ResultType.SUCCESS)

    @classmethod
    def fail(cls, output=None):
        """
        Returns a response as the task has been
        successfully processed.

        Args:
            output (str): Optional output message to set the reason of failure
                within the task object.
        """
        return cls(ResultType.FAIL, output=output)


class BackgroundResponse(_Response):
    """
    Returns the result of a background event processing.
    """

    def __init__(self, status, countdown=30, output=None):
        super().__init__(status, output)
        self.countdown = 30 if countdown < 30 else countdown

    @classmethod
    def skip(cls, output=None):
        """
        Returns a response as the extension wants to skip the processing
        of the received task.

        Args:
            output (str): Optional output message to set the reason of why this
                task has been skipped.
        """
        return cls(ResultType.SKIP, output=output)

    @classmethod
    def reschedule(cls, countdown=30):
        """
        Returns a response as the extension wants to reschedule this task.

        Args:
            countdown (int): Optional amount of seconds before next delivery
                of this task (default to 30 seconds).
        """
        return cls(ResultType.RESCHEDULE, countdown=countdown)

    @classmethod
    def slow_process_reschedule(cls, countdown=300):
        """
        Returns a response as the extension wants to reschedule this task.

        Args:
            countdown (int): Optional amount of seconds before next delivery
                of this task (default to 300 seconds).

        !!! note
            The minumum amount of seconds to wait before this task will
            be redelivered is 300 seconds (5 minutes).
        """
        return cls(
            ResultType.RESCHEDULE,
            countdown=300 if countdown < 300 else countdown,
        )


class ProcessingResponse(BackgroundResponse):
    pass


class InteractiveResponse(_Response):
    """
    Returns the result of an interactive event processing.
    """
    def __init__(self, status, http_status, headers, body, output):
        super().__init__(status, output)
        self.http_status = http_status
        self.headers = headers
        self.body = body

    @property
    def data(self):
        return {
            'http_status': self.http_status,
            'headers': self.headers,
            'body': self.body,
        }

    @classmethod
    def done(cls, http_status=200, headers=None, body=None):
        """
        Returns a response as the extension has successfully
        processed this interactive event.

        Args:
            http_status (int): Optional http status to return to the
                caller (default 200 -> ok).
            headers (Dict): Optional response headers to return to the
                caller.
            body (Dict): Optional response body to return to the caller.
        """
        return cls(ResultType.SUCCESS, http_status, headers, body, None)

    @classmethod
    def fail(cls, http_status=400, headers=None, body=None, output=None):
        """
        Returns a response as the extension has failed to
        process this interactive event.

        Args:
            http_status (int): Optional http status to return to the
                caller (default 400 -> bad request).
            headers (Dict): Optional response headers to return to the
                caller.
            body (Dict): Optional response body to return to the caller.
            output (str): Optional output message to set within the task.
        """
        return cls(ResultType.FAIL, http_status, headers, body, output)


class ValidationResponse(InteractiveResponse):
    def __init__(self, status, data, output=None):
        http_status = 200 if status == ResultType.SUCCESS else 400
        super().__init__(status, http_status, None, data, output)

    @classmethod
    def done(cls, data):
        return cls(ResultType.SUCCESS, data)

    @classmethod
    def fail(cls, data=None, output=None):
        return cls(ResultType.FAIL, data=data, output=output)


class CustomEventResponse(InteractiveResponse):
    pass


class ProductActionResponse(InteractiveResponse):
    pass


class ScheduledExecutionResponse(_Response):
    """
    Returns the result of a scheduled event processing.
    """

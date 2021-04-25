from facebook_business.exceptions import FacebookRequestError
from .logging import logger

# This class hold facebook sdk batch objects, so we don't have to worry about
# the batch size limits - instead we can just call get_batch() and it gives us
# new ones as necessary.


class Batch():
    # Facebook's max batch size is 50,
    # and I see no reason to use a smaller size
    BATCH_SIZE = 50

    # api - Facebook API
    # results_container - if provided, we put the responses into this container
    #                     using .append()
    # raise_exceptions - if True, any facebook request exception will be raised
    #                    and stop the rest of the api calls from continuing,
    #                    rather than just dumping
    def __init__(
        self,
        api,
        results_container=None,
        raise_exceptions=False,
        exceptions_container=None
    ):
        self._api = api
        self._batches = []
        self._batches_metadata = []
        if results_container is None:
            self._results_container = []
        else:
            self._results_container = results_container

        if exceptions_container is None:
            self._exceptions_container = []
        else:
            self._exceptions_container = exceptions_container

        self._raise_exceptions = raise_exceptions
        self._first_exception = None

    # This is kind of a hack.
    # If you want to correlate some piece of data with each api response,
    # you can call batcher.add_metadata(some_data_here) after the API call
    # in which you call batcher.get_batch().
    # This will make it so every entry in results_container
    # has the metadata with it in a tuple.
    def add_metadata(self, metadata):
        self._batches_metadata.append(metadata)

    def execute(self):
        metadata_index = 0
        for i, batch in enumerate(self._batches):
            # In each batch, set the callbacks to this batch container's cbs.
            # This makes it so the user doesn't have to specify the cbs when
            # they use a creation function. Plus, some creation functions
            # in the sdk don't take success_callback and failure_callback
            # params for some reason, which is a real pain to deal.
            # If we do that here it makes life easier

            for j in range(len(batch)):
                if len(self._batches_metadata) > metadata_index:
                    meta = self._batches_metadata[metadata_index]
                    # Capture metadata in a closure. If we try to naively use
                    # the metadata index without capturing it in a closure then
                    # we'll end up with success_callback being called with the
                    # last metadata item.

                    def make_success_callback(meta):
                        def new_success_callback(result):
                            self.success_callback(result, meta)
                        return new_success_callback

                    def make_failure_callback(meta):
                        def new_failure_callback(result):
                            self.failure_callback(result, meta)
                        return new_failure_callback

                    batch._success_callbacks[j] = make_success_callback(meta)
                    batch._failure_callbacks[j] = make_failure_callback(meta)
                else:
                    batch._success_callbacks[j] = self.success_callback
                    batch._failure_callbacks[j] = self.failure_callback
                    metadata_index += 1

            batch.execute()
        if self._raise_exceptions and self._first_exception:
            raise self._first_exception
        return self._results_container

    # This is to implement 'with' statement context management. Ex:
    # with Batch(api) as b:
    #     creator.build_adsets(adset_specs, b.get_batch())
    #     creator.build_ads(ad_specs, b.get_batch())
    # ...
    # and upon exiting the 'with' context the batches will be executed.
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.execute()

    def success_callback(self, result, metadata=None):
        if metadata:
            self._results_container.append((result.json(), metadata))
        else:
            self._results_container.append(result.json())

    def failure_callback(self, result, metadata=None):
        if self._raise_exceptions and not self._first_exception:
            self._first_exception = FacebookRequestError(
                "Batch call failed", {}, 0, {}, result.json())

        if metadata:
            self._exceptions_container.append((result.json(), metadata))
        else:
            self._exceptions_container.append(result.json())

        logger.info(result.json())

    def get_batch(self, metadata=None):
        # If we don't have a batch yet, make one
        if len(self._batches) == 0:
            self._batches.append(self._api.new_batch())

        # If we have batches but the most recent one has reached its max,
        # make a new one
        elif len(self._batches[-1]) >= self.BATCH_SIZE:
            self._batches.append(self._api.new_batch())

        if metadata is not None:
            self.add_metadata(metadata)

        return self._batches[-1]

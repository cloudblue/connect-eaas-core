class EventType:
    ASSET_PURCHASE_REQUEST_PROCESSING = 'asset_purchase_request_processing'
    ASSET_CHANGE_REQUEST_PROCESSING = 'asset_change_request_processing'
    ASSET_SUSPEND_REQUEST_PROCESSING = 'asset_suspend_request_processing'
    ASSET_RESUME_REQUEST_PROCESSING = 'asset_resume_request_processing'
    ASSET_CANCEL_REQUEST_PROCESSING = 'asset_cancel_request_processing'
    ASSET_ADJUSTMENT_REQUEST_PROCESSING = 'asset_adjustment_request_processing'
    ASSET_PURCHASE_REQUEST_VALIDATION = 'asset_purchase_request_validation'
    ASSET_CHANGE_REQUEST_VALIDATION = 'asset_change_request_validation'
    PRODUCT_ACTION_EXECUTION = 'product_action_execution'
    PRODUCT_CUSTOM_EVENT_PROCESSING = 'product_custom_event_processing'
    TIER_CONFIG_SETUP_REQUEST_PROCESSING = 'tier_config_setup_request_processing'
    TIER_CONFIG_CHANGE_REQUEST_PROCESSING = 'tier_config_change_request_processing'
    TIER_CONFIG_ADJUSTMENT_REQUEST_PROCESSING = 'tier_config_adjustment_request_processing'
    TIER_CONFIG_SETUP_REQUEST_VALIDATION = 'tier_config_setup_request_validation'
    TIER_CONFIG_CHANGE_REQUEST_VALIDATION = 'tier_config_change_request_validation'
    SCHEDULED_EXECUTION = 'scheduled_execution'
    LISTING_NEW_REQUEST_PROCESSING = 'listing_new_request_processing'
    LISTING_REMOVE_REQUEST_PROCESSING = 'listing_remove_request_processing'
    TIER_ACCOUNT_UPDATE_REQUEST_PROCESSING = 'tier_account_update_request_processing'
    USAGE_FILE_REQUEST_PROCESSING = 'usage_file_request_processing'
    PART_USAGE_FILE_REQUEST_PROCESSING = 'part_usage_file_request_processing'


class TaskCategory:
    BACKGROUND = 'background'
    INTERACTIVE = 'interactive'
    SCHEDULED = 'scheduled'
    TRANSFORMATION = 'transformation'


class ResultType:
    SUCCESS = 'success'
    RESCHEDULE = 'reschedule'
    SKIP = 'skip'
    RETRY = 'retry'
    FAIL = 'fail'
    DELETE = 'delete'

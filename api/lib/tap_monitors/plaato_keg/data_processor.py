from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from db import async_session_scope
from db.plaato_data import PlaatoData as PlaatoDataDB
from lib.config import Config
from lib import logging, time
from lib.tap_monitors.plaato_keg import plaato_protocol, blynk_protocol, plaato_data

LOGGER = logging.getLogger(__name__)
CONFIG = Config()

class DataProcessor:
    """Processes incoming keg data and distributes to various handlers"""
    
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.device_id: Optional[str] = None
        
    async def process_data(self, raw_data: bytes):
        """Process incoming raw data from keg"""
        try:
            decoded_data = self._decode(raw_data)
            await self._process_decoded(decoded_data)
        except Exception:
            LOGGER.error(f"Error processing keg data.  Raw data: {raw_data}", stack_info=True, exc_info=True)
            
    def _decode(self, data: bytes) -> List[tuple]:
        """Decode raw data through the protocol layers"""
        messages = blynk_protocol.decode(data)
        processed = plaato_protocol.decode_list(messages)
        decoded = plaato_data.decode_list(processed)
        return decoded
        
    async def _process_decoded(self, decoded_data: List[tuple]):
        """Process decoded data and publish to handlers"""
        LOGGER.debug(f"processing decoded keg data: {decoded_data}")
        if not decoded_data:
            LOGGER.debug("no data to process")
            return
            
        data_dict = dict(decoded_data)
        
        if 'id' in data_dict.keys():
            self.device_id = data_dict.pop('id')
            await self._save_to_db(self.device_id, data_dict)
            return
            
        if not self.device_id:
            LOGGER.warning(f"No keg ID found for decoded data: {decoded_data}")
            return
            
        LOGGER.debug(f"Decoded keg data: {decoded_data}")        
        await self._save_to_db(self.device_id, data_dict)

    async def _save_to_db(self, device_id: str, data: Dict[str, Any]):
        """Publish data to all registered handlers"""
        
        LOGGER.debug(f"saving to database.  device_id: {device_id}, data: {data}")
        if not data:
            LOGGER.debug(f"ignoring, nothing to write to DB.  device_id: {device_id}, data: {data}")
        
        data["last_updated_on"] = datetime.now(timezone.utc)
        async with async_session_scope(CONFIG) as db_session:
            LOGGER.debug(f"Updating DB record for keg {device_id}.  Data: {data}")
            rowcnt = await PlaatoDataDB.update(db_session, device_id, **data)
            LOGGER.debug(f"Rows affected: {rowcnt}")
            if rowcnt == 0:
                LOGGER.warning(f"No record update for keg {device_id}, attempting to insert new record.")
                await PlaatoDataDB.create(db_session, id=device_id, **data)
                LOGGER.info(f"Record created successfully!  Id: {device_id}")
            else:
                LOGGER.info(f"DB updated successfully for keg {device_id}")

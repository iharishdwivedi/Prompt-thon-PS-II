/**
 * OwnerRegistry Component
 * Feature C — Floor plan ownership registry
 * Calls: GET /api/get_owner/:hash
 * Contract function: get_owner(floor_hash) → Option<Address>
 */
import { getOwner } from '../App.js';

export class OwnerRegistry {
    async lookup(floorHash) {
        return getOwner(floorHash);
    }
}

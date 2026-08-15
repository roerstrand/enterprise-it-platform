import { Role } from '../auth/current-user';

// email/role är bara satta när svaret kommer från en Admin - se api_list_users i routers/demo.py,
// som strippar dem för alla andra roller (bara id+name behövs t.ex. för att slå upp författarnamn)
export interface User {
    id: number;
    name: string;
    email?: string;
    role?: Role;
}

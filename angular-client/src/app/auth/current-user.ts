// Roller i stigande behörighet: viewer (läsrätt) < operator (hanterar CI/incident/change) < admin (allt, inkl. audit + roller)
export type Role = 'admin' | 'operator' | 'viewer';

export interface CurrentUser {
    id: number;
    email: string;
    role: Role;
}

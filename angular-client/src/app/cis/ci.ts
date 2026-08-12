export interface CI  {
    id: number;
    name: string;
    ci_type: string;
    environment: string;
    owner_team_id: number | null;
    owner_user_id: number | null;
}
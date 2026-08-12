import { Routes } from '@angular/router';
import { UsersList } from './users/users-list';
import { CisList } from './cis/cis-list';
import { IncidentsList } from './incidents/incidents-list';

export const routes: Routes = [
    { path: 'users', component: UsersList },
    { path: 'cis', component: CisList },
    { path: 'incidents', component: IncidentsList },
    { path: '', redirectTo: 'users', pathMatch: 'full' }
];

import { Routes } from '@angular/router';
import { UsersList } from './users/users-list';
import { CisList } from './cis/cis-list';
import { IncidentsList } from './incidents/incidents-list';
import { IncidentDetail } from './incidents/incident-detail/incident-detail';
import { Login } from './auth/login/login';
import { Register } from './auth/register/register';
import { Dashboard } from './dashboard/dashboard';
import { AuditLog } from './audit/audit-log';
import { authGuard, adminGuard } from './auth/auth.guard';

export const routes: Routes = [
    { path: 'login', component: Login },
    { path: 'register', component: Register },
    { path: 'dashboard', component: Dashboard, canActivate: [authGuard] },
    { path: 'users', component: UsersList, canActivate: [adminGuard] },
    { path: 'cis', component: CisList, canActivate: [authGuard] },
    { path: 'incidents', component: IncidentsList, canActivate: [authGuard] },
    { path: 'incidents/:id', component: IncidentDetail, canActivate: [authGuard] },
    { path: 'audit', component: AuditLog, canActivate: [adminGuard] },
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
];

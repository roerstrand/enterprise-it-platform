import { Routes } from '@angular/router';
import { UsersList } from './users/users-list';
import { CisList } from './cis/cis-list';

export const routes: Routes = [
    { path: 'users', component: UsersList },
    { path: 'cis', component: CisList },
    { path: '', redirectTo: 'users', pathMatch: 'full' }
];

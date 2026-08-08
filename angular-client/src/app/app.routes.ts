import { Routes } from '@angular/router';
import { UsersList } from './users/users-list';

export const routes: Routes = [
    { path: 'users, component: UsersList' },
    { path: '', redirectTo: 'users', pathMatch: 'full' }
];

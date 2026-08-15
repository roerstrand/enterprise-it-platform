import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { UserService } from './user.service';
import { User } from './user';
import { Role } from '../auth/current-user';
import { AuthService } from '../auth/auth.service';

@Component({
    selector: 'app-users-list',
    imports: [FormsModule, MatTableModule, MatProgressSpinnerModule, MatCardModule, MatIconModule, MatSelectModule],
    templateUrl: './users-list.html',
    styleUrl: './users-list.scss'
})

export class UsersList implements OnInit {
    protected readonly users = signal<User[]>([]);
    protected readonly loading = signal(true);
    protected readonly roles: Role[] = ['admin', 'operator', 'viewer'];

    constructor(private userService: UserService, protected authService: AuthService) {}

    protected get displayedColumns(): string[] {
        // Admin ser en extra kolumn för att kunna ändra andra användares roll
        return this.authService.isAdmin() ? ['id', 'name', 'email', 'role'] : ['id', 'name', 'email', 'role_readonly'];
    }

    ngOnInit(): void {
        this.loadUsers();
    }

    private loadUsers(): void {
        this.userService.list().subscribe({
            next: (users) => {
                this.users.set(users);
                this.loading.set(false);
            },
            error: () => {
                this.loading.set(false);
            }
        });
    }

    protected onRoleChange(user: User, role: Role): void {
        this.userService.updateRole(user.id, role).subscribe({
            next: () => this.loadUsers()
        });
    }
}

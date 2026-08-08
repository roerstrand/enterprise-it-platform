import { Component, OnInit, signal } from '@angular/core';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { UserService } from './user.service';
import { User } from './user';

@Component({
    selector: 'app-users-list',
    imports: [MatTableModule, MatProgressSpinnerModule],
    templateUrl: './users-list.html',
    styleUrl: './users-list.scss'
})

export class UsersList implements OnInit {
    protected readonly users = signal<User[]>([]);
    protected readonly loading = signal(true);
    protected readonly displayedColumns = ['id', 'name', 'email'];

    constructor(private userService: UserService) {}

    ngOnInit(): void {
        this.userService.list().subscribe({
            next: (users) => {
                this.users.set(users);
                this.loading.set(false);
            },
            error: () => {
                this.loading.set(false);
            }
        })
    }
}
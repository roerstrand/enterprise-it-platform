import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ChangeService } from '../change.service';
import { ChangeDetail } from '../change-detail';
import { AuthService } from '../../auth/auth.service';

@Component({
    selector: 'app-change-detail',
    imports: [RouterLink, MatCardModule, MatIconModule, MatButtonModule, MatProgressSpinnerModule],
    templateUrl: './change-detail.html',
    styleUrl: './change-detail.scss',
})
export class ChangeDetailPage implements OnInit {
    protected readonly change = signal<ChangeDetail | null>(null);
    protected readonly loading = signal(true);
    protected readonly notFound = signal(false);

    private changeId!: number;

    constructor(
        private route: ActivatedRoute,
        private changeService: ChangeService,
        private snackBar: MatSnackBar,
        protected authService: AuthService,
    ) {}

    ngOnInit(): void {
        this.changeId = Number(this.route.snapshot.paramMap.get('id'));
        this.load();
    }

    private load(): void {
        this.loading.set(true);
        this.changeService.getById(this.changeId).subscribe({
            next: (change) => {
                this.change.set(change);
                this.loading.set(false);
            },
            error: () => {
                this.notFound.set(true);
                this.loading.set(false);
            },
        });
    }

    protected onApprove(): void {
        this.changeService.approve(this.changeId).subscribe({
            next: () => this.load(),
            error: (err) => this.snackBar.open(err?.error?.detail || 'Could not approve change.', 'Dismiss', { duration: 5000 }),
        });
    }

    protected statusClass(status: string): string {
        return `chip chip-status-${(status || '').toLowerCase()}`;
    }

    protected severityClass(severity: string): string {
        return `chip chip-severity-${(severity || '').toLowerCase()}`;
    }
}

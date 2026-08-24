import { Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TitleCasePipe } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ChangeService } from './change.service';
import { Change } from './change';
import { CIService } from '../cis/ci.service';
import { CI } from '../cis/ci';
import { AuthService } from '../auth/auth.service';

@Component({
    selector: 'app-changes-list',
    imports: [
        ReactiveFormsModule,
        RouterLink,
        TitleCasePipe,
        MatTableModule,
        MatProgressSpinnerModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatCardModule,
        MatIconModule,
    ],
    templateUrl: './changes-list.html',
    styleUrl: './changes-list.scss',
})
export class ChangesList implements OnInit {
    protected readonly changes = signal<Change[]>([]);
    protected readonly cis = signal<CI[]>([]);
    protected readonly loading = signal(true);
    protected readonly displayedColumns = ['id', 'title', 'status', 'risk_level', 'ci_id', 'actions'];
    protected readonly riskLevels = ['low', 'medium', 'high'];

    protected readonly createForm: FormGroup;

    constructor(
        private changeService: ChangeService,
        private ciService: CIService,
        private snackBar: MatSnackBar,
        formBuilder: FormBuilder,
        protected authService: AuthService,
    ) {
        this.createForm = formBuilder.group({
            title: ['', Validators.required],
            description: ['', Validators.required],
            riskLevel: ['', Validators.required],
            ciId: [null, Validators.required],
        });
    }

    ngOnInit(): void {
        this.load();
        this.ciService.list().subscribe({ next: (cis) => this.cis.set(cis) });
    }

    protected ciLabel(ci: CI): string {
        return `${ci.name} (${ci.ci_type} · ${ci.environment})`;
    }

    private load(): void {
        this.loading.set(true);
        this.changeService.list().subscribe({
            next: (changes) => {
                this.changes.set(changes);
                this.loading.set(false);
            },
            error: () => this.loading.set(false),
        });
    }

    private showError(err: { error?: { detail?: string } }, fallback: string): void {
        this.snackBar.open(err?.error?.detail || fallback, 'Dismiss', { duration: 5000 });
    }

    protected onCreateSubmit(): void {
        if (this.createForm.invalid) return;
        const { title, description, riskLevel, ciId } = this.createForm.value;
        this.changeService.create(title, description, riskLevel, ciId).subscribe({
            next: () => {
                this.createForm.reset();
                this.load();
            },
            error: (err) => this.showError(err, 'Could not create change.'),
        });
    }

    protected onApprove(changeId: number): void {
        this.changeService.approve(changeId).subscribe({
            next: () => this.load(),
            error: (err) => this.showError(err, 'Could not approve change.'),
        });
    }

    protected statusClass(status: string): string {
        return `chip chip-status-${(status || '').toLowerCase()}`;
    }
}

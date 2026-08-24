import { Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { CIService } from './ci.service';
import { CI } from './ci';
import { AuthService } from '../auth/auth.service';

@Component({
    selector: 'app-cis-list',
    imports: [
        ReactiveFormsModule,
        RouterLink,
        MatTableModule,
        MatProgressSpinnerModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatCardModule,
        MatIconModule
    ],
    templateUrl: './cis-list.html',
    styleUrl: './cis-list.scss'
})

export class CisList implements OnInit {
    protected readonly cis = signal<CI[]>([]);
    protected readonly loading = signal(true);
    protected readonly displayedColumns = ['id', 'name', 'ci_type', 'environment', 'owner_user_id', 'actions'];

    protected readonly editingId = signal<number | null>(null);

    protected readonly form: FormGroup;
    protected readonly editForm: FormGroup;

    constructor(private ciService: CIService, formBuilder: FormBuilder, protected authService: AuthService) {
        this.form = formBuilder.group({
            name: ['', Validators.required],
            ciType: ['', Validators.required],
            environment: ['', Validators.required],
            ownerUserId: [null],
        });
        this.editForm = formBuilder.group({
            name: ['', Validators.required],
            ciType: ['', Validators.required],
            environment: ['', Validators.required],
            ownerUserId: [null],
        });

    }

    ngOnInit(): void {
        this.loadCis();
    }

    private loadCis(): void {
        this.loading.set(true);
        this.ciService.list().subscribe({
            next: (cis) => {
                this.cis.set(cis);
                this.loading.set(false)
            },
            error: () => {
                this.loading.set(false)
            }
        });
    }

    protected onSubmit(): void {
        if (this.form.invalid) {
            return;
        }

        const { name, ciType, environment, ownerUserId } = this.form.value;
        this.ciService.create(name, ciType, environment, ownerUserId).subscribe({
            next: () => {
                this.form.reset();
                this.loadCis();
            }
        });
    }

     protected onEditClick(ci: CI): void {
        this.editingId.set(ci.id);
        this.editForm.patchValue({
            name: ci.name,
            ciType: ci.ci_type,
            environment: ci.environment,
            ownerUserId: ci.owner_user_id
        });
    }

    protected onEditCancel(): void {
        this.editingId.set(null);
    }

    protected onEditSubmit(): void {
        const id = this.editingId();
        if (id === null || this.editForm.invalid) {
            return;
        }
        const { name, ciType, environment, ownerUserId } = this.editForm.value;
        this.ciService.update(id, name, ciType, environment, ownerUserId).subscribe({
            next: () => {
                this.editingId.set(null);
                this.loadCis();
            }
        });
    }

    protected onDelete(ciId: number): void {
        if (!confirm(`Delete CI ${ciId}?`)) {
            return;
        }
        this.ciService.delete(ciId).subscribe({
            next: () => this.loadCis()
        });
    }
}


import { Component, OnInit, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { CIService } from './ci.service';
import { CI } from './ci';

@Component({
    selector: 'app-cis-list',
    imports: [
        ReactiveFormsModule,
        MatTableModule,
        MatProgressSpinnerModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule
    ],
    templateUrl: './cis-list.html',
    styleUrl: './cis-list.scss'
})

export class CisList implements OnInit {
    protected readonly cis = signal<CI[]>([]);
    protected readonly loading = signal(true);
    protected readonly displayedColumns = ['id', 'name', 'ci_type', 'environment', 'owner_user_id'];

    protected readonly form: FormGroup;

    constructor(private ciService: CIService, formBuilder: FormBuilder) {
        this.form = formBuilder.group({
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
}


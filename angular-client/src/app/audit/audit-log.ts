import { Component, OnInit, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { DatePipe, JsonPipe } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuditService } from './audit.service';
import { AuditEvent } from './audit-event';

@Component({
    selector: 'app-audit-log',
    imports: [
        ReactiveFormsModule,
        DatePipe,
        JsonPipe,
        MatTableModule,
        MatCardModule,
        MatIconModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatProgressSpinnerModule,
    ],
    templateUrl: './audit-log.html',
    styleUrl: './audit-log.scss',
})
export class AuditLog implements OnInit {
    protected readonly events = signal<AuditEvent[]>([]);
    protected readonly loading = signal(true);
    protected readonly displayedColumns = ['timestamp', 'actor', 'action', 'entity', 'changes'];
    protected readonly entityTypes = ['incident', 'ci', 'change'];

    protected readonly filterForm: FormGroup;

    constructor(private auditService: AuditService, formBuilder: FormBuilder) {
        this.filterForm = formBuilder.group({
            entityType: [''],
            entityId: [''],
            action: [''],
        });
    }

    ngOnInit(): void {
        this.load();
    }

    protected onFilterSubmit(): void {
        this.load();
    }

    protected onFilterReset(): void {
        this.filterForm.reset({ entityType: '', entityId: '', action: '' });
        this.load();
    }

    private load(): void {
        this.loading.set(true);
        const { entityType, entityId, action } = this.filterForm.value;
        this.auditService.list({ entityType, entityId, action }).subscribe({
            next: (events) => {
                this.events.set(events);
                this.loading.set(false);
            },
            error: () => this.loading.set(false),
        });
    }
}

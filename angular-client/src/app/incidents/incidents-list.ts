import { Component, OnInit, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { IncidentService } from './incident.service';
import { Incident } from './incident';

@Component({
    selector: 'app-incidents-list',
    imports: [
        ReactiveFormsModule,
        MatTableModule,
        MatProgressSpinnerModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule
    ], 
    templateUrl: './incidents-list.html',
    styleUrl: './incidents-list.scss'
})

export class IncidentsList implements OnInit {
    protected readonly incidents = signal<Incident[]>([]);
    protected readonly loading = signal(true);
    protected readonly displayedColumns = [
      'id', 'title', 'description', 'status', 'severity', 'ai_suggested_severity', 'ai_suggested_status', 'ai_summary', 'actions'
    ];

    // null = inget under redigering, annars id:t för raden vars edit-formulär ska visas
    protected readonly editingId = signal<number | null>(null);

    protected readonly createForm: FormGroup;
    protected readonly updateForm: FormGroup;
    protected readonly editForm: FormGroup;

    constructor(private incidentService: IncidentService, formBuilder: FormBuilder) {
        this.createForm = formBuilder.group({
            title: ['', Validators.required],
            description: ['', Validators.required],
            severity: ['', Validators.required],
            ciId: [null, Validators.required]
        });

        this.updateForm = formBuilder.group({
            incidentId: [null, Validators.required],
            text: ['', Validators.required]
        });

        this.editForm = formBuilder.group({
            title: ['', Validators.required],
            description: ['', Validators.required],
            severity: ['', Validators.required],
            ciId: [null, Validators.required]
        });
    }

    ngOnInit(): void {
        this.loadIncidents();
    }

    private loadIncidents(): void {
        this.loading.set(true);
        this.incidentService.list().subscribe({
            next: (incidents) => {
                this.incidents.set(incidents);
                this.loading.set(false);
            },
            error: () => {
                this.loading.set(false);
            }
        });
    }

    protected onCreateSubmit(): void {
        if (this.createForm.invalid) {
            return;
        }
        const { title, description, severity, ciId } = this.createForm.value;
        this.incidentService.create(title, description, severity, ciId).subscribe({
            next: () => {
                this.createForm.reset();
                this.loadIncidents();
            }
        });
    }

    protected onUpdateSubmit(): void {
        if (this.updateForm.invalid) {
            return;
        }
        const { incidentId, text } = this.updateForm.value;
        this.incidentService.addUpdate(incidentId, text).subscribe({
            next: () => {
                this.updateForm.reset();
                this.loadIncidents();
            }
        });
    }

    protected onAcceptSeverity(incidentId: number): void {
        this.incidentService.acceptSeverity(incidentId).subscribe({
            next: () => this.loadIncidents()
        });
    }

    protected onAcceptStatus(incidentId: number): void {
        this.incidentService.acceptStatus(incidentId).subscribe({
            next: () => this.loadIncidents()
        });
    }

    protected onEditClick(incident: Incident): void {
        this.editingId.set(incident.id);
        // patchValue fyller bara i de nämnda fälten, till skillnad från setValue som kräver ALLA fält
        this.editForm.patchValue({
            title: incident.title,
            description: incident.description,
            severity: incident.severity,
            ciId: incident.ci_id
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
        const { title, description, severity, ciId } = this.editForm.value;
        this.incidentService.update(id, title, description, severity, ciId).subscribe({
            next: () => {
                this.editingId.set(null);
                this.loadIncidents();
            }
        });
    }

    protected onDelete(incidentId: number): void {
        if (!confirm(`Delete incident ${incidentId}?`)) {
            return;
        }
        this.incidentService.delete(incidentId).subscribe({
            next: () => this.loadIncidents()
        });
    }
}
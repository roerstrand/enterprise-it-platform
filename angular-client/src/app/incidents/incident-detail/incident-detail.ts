import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { DatePipe, TitleCasePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { IncidentService } from '../incident.service';
import { IncidentUpdate, IncidentWithCI } from '../incident';
import { UserService } from '../../users/user.service';
import { User } from '../../users/user';
import { AuthService } from '../../auth/auth.service';

// Måste spegla server/domain/incident_lifecycle.py ALLOWED_TRANSITIONS - enforcement sker
// alltid server-side, detta styr bara vilka knappar som visas/är aktiva i UI:t.
const ALLOWED_TRANSITIONS: Record<string, string[]> = {
    open: ['in_progress'],
    in_progress: ['resolved'],
    resolved: ['closed'],
    closed: [],
};

@Component({
    selector: 'app-incident-detail',
    imports: [
        ReactiveFormsModule,
        RouterLink,
        TitleCasePipe,
        DatePipe,
        MatCardModule,
        MatIconModule,
        MatButtonModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatProgressSpinnerModule,
    ],
    templateUrl: './incident-detail.html',
    styleUrl: './incident-detail.scss',
})
export class IncidentDetail implements OnInit {
    protected readonly incident = signal<IncidentWithCI | null>(null);
    protected readonly updates = signal<IncidentUpdate[]>([]);
    protected readonly loading = signal(true);
    protected readonly notFound = signal(false);
    protected readonly severities = ['low', 'medium', 'high', 'critical'];
    protected readonly usersById = signal<Map<number, User>>(new Map());

    protected readonly updateForm: FormGroup;
    protected readonly severityForm: FormGroup;

    private incidentId!: number;

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private incidentService: IncidentService,
        private userService: UserService,
        formBuilder: FormBuilder,
        protected authService: AuthService,
    ) {
        this.updateForm = formBuilder.group({ text: ['', Validators.required] });
        this.severityForm = formBuilder.group({ severity: ['', Validators.required] });
    }

    ngOnInit(): void {
        this.incidentId = Number(this.route.snapshot.paramMap.get('id'));

        this.userService.list().subscribe({
            next: (users) => this.usersById.set(new Map(users.map((u) => [u.id, u]))),
        });

        this.load();
    }

    private load(): void {
        this.loading.set(true);
        this.incidentService.getById(this.incidentId).subscribe({
            next: (incident) => {
                this.incident.set(incident);
                this.severityForm.patchValue({ severity: incident.severity }, { emitEvent: false });
                this.loading.set(false);
            },
            error: () => {
                this.notFound.set(true);
                this.loading.set(false);
            },
        });
        this.incidentService.getUpdates(this.incidentId).subscribe({
            next: (updates) => this.updates.set(updates),
        });
    }

    protected authorLabel(update: IncidentUpdate): string {
        if (!update.author_user_id) return 'System / AI';
        return this.usersById().get(update.author_user_id)?.name ?? `User #${update.author_user_id}`;
    }

    // Nästa giltiga statusar enligt lifecycle-grafen ovan - tomt för closed (terminal)
    protected nextStatuses(): string[] {
        const current = this.incident()?.status ?? '';
        return ALLOWED_TRANSITIONS[current] ?? [];
    }

    protected onTransitionTo(status: string): void {
        this.incidentService.updateStatus(this.incidentId, status).subscribe({
            next: () => this.load(),
        });
    }

    protected onSeveritySubmit(): void {
        if (this.severityForm.invalid) return;
        const { severity } = this.severityForm.value;
        this.incidentService.updateSeverity(this.incidentId, severity).subscribe({
            next: () => this.load(),
        });
    }

    protected onAcceptSeverity(): void {
        this.incidentService.acceptSeverity(this.incidentId).subscribe({ next: () => this.load() });
    }

    protected onAcceptStatus(): void {
        this.incidentService.acceptStatus(this.incidentId).subscribe({ next: () => this.load() });
    }

    protected onUpdateSubmit(): void {
        if (this.updateForm.invalid) return;
        const { text } = this.updateForm.value;
        this.incidentService.addUpdate(this.incidentId, text).subscribe({
            next: () => {
                this.updateForm.reset();
                this.load();
            },
        });
    }

    protected severityClass(severity: string): string {
        return `chip chip-severity-${(severity || '').toLowerCase()}`;
    }

    protected statusClass(status: string): string {
        return `chip chip-status-${(status || '').toLowerCase()}`;
    }
}

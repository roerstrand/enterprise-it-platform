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
import { MatSnackBar } from '@angular/material/snack-bar';
import { IncidentService } from '../incident.service';
import { IncidentUpdate, IncidentWithCI } from '../incident';
import { UserService } from '../../users/user.service';
import { User } from '../../users/user';
import { ChangeService } from '../../changes/change.service';
import { Change } from '../../changes/change';
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
    protected readonly users = signal<User[]>([]);
    protected readonly usersById = signal<Map<number, User>>(new Map());
    protected readonly linkedChanges = signal<Change[]>([]);
    protected readonly allChanges = signal<Change[]>([]);
    protected readonly riskLevels = ['low', 'medium', 'high'];

    protected readonly updateForm: FormGroup;
    protected readonly severityForm: FormGroup;
    protected readonly assigneeForm: FormGroup;
    protected readonly linkChangeForm: FormGroup;
    protected readonly newChangeForm: FormGroup;

    private incidentId!: number;

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private incidentService: IncidentService,
        private userService: UserService,
        private changeService: ChangeService,
        private snackBar: MatSnackBar,
        formBuilder: FormBuilder,
        protected authService: AuthService,
    ) {
        this.updateForm = formBuilder.group({ text: ['', Validators.required] });
        this.severityForm = formBuilder.group({ severity: ['', Validators.required] });
        this.assigneeForm = formBuilder.group({ assigneeUserId: [null] });
        this.linkChangeForm = formBuilder.group({ changeId: [null, Validators.required] });
        this.newChangeForm = formBuilder.group({
            title: ['', Validators.required],
            description: ['', Validators.required],
            riskLevel: ['', Validators.required],
        });
    }

    ngOnInit(): void {
        this.incidentId = Number(this.route.snapshot.paramMap.get('id'));

        this.userService.list().subscribe({
            next: (users) => {
                this.users.set(users);
                this.usersById.set(new Map(users.map((u) => [u.id, u])));
            },
        });

        this.changeService.list().subscribe({
            next: (changes) => this.allChanges.set(changes),
        });

        this.load();
    }

    private load(): void {
        this.loading.set(true);
        this.incidentService.getById(this.incidentId).subscribe({
            next: (incident) => {
                this.incident.set(incident);
                this.severityForm.patchValue({ severity: incident.severity }, { emitEvent: false });
                this.assigneeForm.patchValue({ assigneeUserId: incident.assignee_user_id }, { emitEvent: false });
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
        this.incidentService.getLinkedChanges(this.incidentId).subscribe({
            next: (changes) => this.linkedChanges.set(changes),
        });
    }

    // Changes redan länkade till incidenten ska inte kunna väljas igen i "link existing"-selecten
    protected linkableChanges(): Change[] {
        const linkedIds = new Set(this.linkedChanges().map((c) => c.id));
        return this.allChanges().filter((c) => !linkedIds.has(c.id));
    }

    protected authorLabel(update: IncidentUpdate): string {
        if (!update.author_user_id) return 'System / AI';
        return this.usersById().get(update.author_user_id)?.name ?? `User #${update.author_user_id}`;
    }

    protected assigneeName(userId: number | null): string {
        if (!userId) return 'Unassigned';
        return this.usersById().get(userId)?.name ?? `User #${userId}`;
    }

    // t.ex. "2h 15m" eller "-45m" (förbi deadline) - remaining_seconds från backend kan vara negativt
    protected formatRemaining(seconds: number): string {
        const sign = seconds < 0 ? '-' : '';
        const abs = Math.abs(seconds);
        const hours = Math.floor(abs / 3600);
        const minutes = Math.floor((abs % 3600) / 60);
        if (hours > 0) return `${sign}${hours}h ${minutes}m`;
        return `${sign}${minutes}m`;
    }

    protected slaClass(state: string): string {
        const map: Record<string, string> = { on_track: 'low', met: 'low', at_risk: 'medium', breached: 'critical' };
        return `chip chip-severity-${map[state] ?? ''}`;
    }

    // Nästa giltiga statusar enligt lifecycle-grafen ovan - tomt för closed (terminal)
    protected nextStatuses(): string[] {
        const current = this.incident()?.status ?? '';
        return ALLOWED_TRANSITIONS[current] ?? [];
    }

    // Utan denna: backendens 409 (t.ex. ogiltig lifecycle-övergång) svaldes helt tyst -
    // knappen såg ut att inte göra något alls, ingen felindikation någonstans.
    private showError(err: { error?: { detail?: string } }, fallback: string): void {
        this.snackBar.open(err?.error?.detail || fallback, 'Dismiss', { duration: 5000 });
    }

    protected onTransitionTo(status: string): void {
        this.incidentService.updateStatus(this.incidentId, status).subscribe({
            next: () => this.load(),
            error: (err) => this.showError(err, 'Could not update status.'),
        });
    }

    protected onSeveritySubmit(): void {
        if (this.severityForm.invalid) return;
        const { severity } = this.severityForm.value;
        this.incidentService.updateSeverity(this.incidentId, severity).subscribe({
            next: () => this.load(),
            error: (err) => this.showError(err, 'Could not update severity.'),
        });
    }

    protected onAssigneeSubmit(): void {
        const { assigneeUserId } = this.assigneeForm.value;
        this.incidentService.assign(this.incidentId, assigneeUserId).subscribe({
            next: () => this.load(),
            error: (err) => this.showError(err, 'Could not update assignee.'),
        });
    }

    protected onAcceptSeverity(): void {
        this.incidentService.acceptSeverity(this.incidentId).subscribe({
            next: () => this.load(),
            error: (err) => this.showError(err, 'Could not accept suggested severity.'),
        });
    }

    protected onAcceptStatus(): void {
        this.incidentService.acceptStatus(this.incidentId).subscribe({
            next: () => this.load(),
            error: (err) => this.showError(err, 'Could not accept suggested status.'),
        });
    }

    protected onUpdateSubmit(): void {
        if (this.updateForm.invalid) return;
        const { text } = this.updateForm.value;
        this.incidentService.addUpdate(this.incidentId, text).subscribe({
            next: () => {
                this.updateForm.reset();
                this.load();
            },
            error: (err) => this.showError(err, 'Could not add update.'),
        });
    }

    protected severityClass(severity: string): string {
        return `chip chip-severity-${(severity || '').toLowerCase()}`;
    }

    protected statusClass(status: string): string {
        return `chip chip-status-${(status || '').toLowerCase()}`;
    }

    protected onLinkChangeSubmit(): void {
        if (this.linkChangeForm.invalid) return;
        const { changeId } = this.linkChangeForm.value;
        this.incidentService.linkChange(this.incidentId, changeId).subscribe({
            next: () => {
                this.linkChangeForm.reset();
                this.load();
            },
            error: (err) => this.showError(err, 'Could not link change.'),
        });
    }

    protected onUnlinkChange(changeId: number): void {
        this.incidentService.unlinkChange(this.incidentId, changeId).subscribe({
            next: () => this.load(),
            error: (err) => this.showError(err, 'Could not unlink change.'),
        });
    }

    protected onNewChangeSubmit(): void {
        if (this.newChangeForm.invalid) return;
        const incident = this.incident();
        if (!incident) return;
        const { title, description, riskLevel } = this.newChangeForm.value;
        // Skapa changen (samma väg som Changes-sidans formulär), länka den sedan till incidenten -
        // inget nytt backend-API bara för det här, återanvänder de två befintliga endpointsen.
        this.changeService.create(title, description, riskLevel, incident.ci_id).subscribe({
            next: (change) => {
                this.incidentService.linkChange(this.incidentId, change.id).subscribe({
                    next: () => {
                        this.newChangeForm.reset();
                        this.changeService.list().subscribe({ next: (changes) => this.allChanges.set(changes) });
                        this.load();
                    },
                    error: (err) => this.showError(err, 'Change created but could not be linked.'),
                });
            },
            error: (err) => this.showError(err, 'Could not create change.'),
        });
    }
}

import { Component, OnInit, signal } from '@angular/core';
import { TitleCasePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { debounceTime, distinctUntilChanged } from 'rxjs';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSnackBar } from '@angular/material/snack-bar';
import { IncidentService } from './incident.service';
import { Incident, IncidentListFilter, IncidentUpdate } from './incident';
import { CIService } from '../cis/ci.service';
import { CI } from '../cis/ci';
import { UserService } from '../users/user.service';
import { User } from '../users/user';
import { AuthService } from '../auth/auth.service';

// Alla filterfält som lever i URL:ens query params - en bokmärkt/delad länk återskapar exakt samma vy.
const FILTER_KEYS = ['status', 'severity', 'assignee', 'ciId', 'slaState', 'search', 'createdAfter', 'createdBefore', 'sortBy', 'sortDir'] as const;

@Component({
    selector: 'app-incidents-list',
    imports: [
        ReactiveFormsModule,
        RouterLink,
        MatTableModule,
        MatProgressSpinnerModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatCardModule,
        MatIconModule,
        MatPaginatorModule,
        TitleCasePipe
    ],
    templateUrl: './incidents-list.html',
    styleUrl: './incidents-list.scss'
})

export class IncidentsList implements OnInit {
    protected readonly incidents = signal<Incident[]>([]);
    protected readonly cis = signal<CI[]>([]);
    protected readonly users = signal<User[]>([]);
    protected readonly usersById = signal<Map<number, User>>(new Map());
    protected readonly loading = signal(true);
    protected readonly totalCount = signal(0);
    protected readonly page = signal(0); // 0-based för MatPaginator
    protected readonly pageSize = signal(25);

    // ai_suggested_severity + ai_suggested_status slås ihop till en kolumn (ai_suggestions) i
    // .html - två separata kolumner tog för mycket bredd för hur sällan/kort innehållet är
    protected readonly displayedColumns = [
      'id', 'title', 'status', 'severity', 'assignee', 'sla', 'ai_suggestions', 'ai_summary', 'actions'
    ];

    // Backend validerar mot exakt dessa värden (server/domain/incident_lifecycle.py:SEVERITIES),
    // lagras alltid lowercase - se severity-selecten i .html
    protected readonly severities = ['low', 'medium', 'high', 'critical'];
    protected readonly statuses = ['open', 'in_progress', 'resolved', 'closed'];
    protected readonly slaStates = ['on_track', 'at_risk', 'breached', 'met'];

    // null = inget under redigering, annars id:t för raden vars edit-formulär ska visas
    protected readonly editingId = signal<number | null>(null);

    // null = ingen updates-historik visas just nu, annars id:t för raden
    protected readonly viewingUpdatesId = signal<number | null>(null);
    protected readonly incidentUpdates = signal<IncidentUpdate[]>([]);

    protected readonly createForm: FormGroup;
    protected readonly updateForm: FormGroup;
    protected readonly editForm: FormGroup;
    protected readonly filterForm: FormGroup;

    constructor(
        private incidentService: IncidentService,
        private ciService: CIService,
        private userService: UserService,
        private snackBar: MatSnackBar,
        private route: ActivatedRoute,
        private router: Router,
        formBuilder: FormBuilder,
        protected authService: AuthService,
    ) {
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

        // assignee: '' = alla, 'me' = tilldelad inloggad användare, 'unassigned' = ej tilldelad,
        // annars ett user-id som sträng - allt matchas om till rätt backend-parametrar i buildFilter()
        this.filterForm = formBuilder.group({
            status: [''],
            severity: [''],
            assignee: [''],
            ciId: [''],
            slaState: [''],
            search: [''],
            createdAfter: [''],
            createdBefore: [''],
            sortBy: ['created_at'],
            sortDir: ['desc'],
        });
    }

    ngOnInit(): void {
        // CI/user-listorna behövs för Create/Edit-formulärens select samt filter-/assignee-dropdowns,
        // ingen loading-state krävs - formulären fungerar (fast tomma) tills de kommit tillbaka
        this.ciService.list().subscribe({
            next: (cis) => this.cis.set(cis)
        });
        this.userService.list().subscribe({
            next: (users) => {
                this.users.set(users);
                this.usersById.set(new Map(users.map((u) => [u.id, u])));
            }
        });

        const params = this.route.snapshot.queryParamMap;
        const initial: Record<string, string> = {};
        for (const key of FILTER_KEYS) {
            if (params.has(key)) initial[key] = params.get(key)!;
        }
        this.filterForm.patchValue(initial, { emitEvent: false });
        this.page.set(Number(params.get('page') ?? 0));
        this.pageSize.set(Number(params.get('pageSize') ?? 25));

        this.loadIncidents();

        this.filterForm.valueChanges.pipe(
            debounceTime(400),
            distinctUntilChanged((a, b) => JSON.stringify(a) === JSON.stringify(b)),
        ).subscribe(() => {
            this.page.set(0);
            this.syncUrlAndLoad();
        });
    }

    // Visningstext i CI-selecten, t.ex. "db-02 (server · production)"
    protected ciLabel(ci: CI): string {
        return `${ci.name} (${ci.ci_type} · ${ci.environment})`;
    }

    protected assigneeName(userId: number | null): string {
        if (!userId) return 'Unassigned';
        return this.usersById().get(userId)?.name ?? `User #${userId}`;
    }

    private buildFilter(): IncidentListFilter {
        const f = this.filterForm.value;
        const filter: IncidentListFilter = {
            status: f.status || undefined,
            severity: f.severity || undefined,
            ci_id: f.ciId ? Number(f.ciId) : undefined,
            sla_state: f.slaState || undefined,
            search: f.search || undefined,
            created_after: f.createdAfter ? new Date(f.createdAfter).toISOString() : undefined,
            created_before: f.createdBefore ? new Date(f.createdBefore).toISOString() : undefined,
            sort_by: f.sortBy || 'created_at',
            sort_dir: f.sortDir || 'desc',
            page: this.page() + 1,
            page_size: this.pageSize(),
        };
        if (f.assignee === 'unassigned') {
            filter.unassigned_only = true;
        } else if (f.assignee === 'me') {
            filter.assignee_user_id = this.authService.currentUser()?.id;
        } else if (f.assignee) {
            filter.assignee_user_id = Number(f.assignee);
        }
        return filter;
    }

    private syncUrlAndLoad(): void {
        const f = this.filterForm.value;
        const queryParams: Record<string, string | null> = {};
        for (const key of FILTER_KEYS) {
            queryParams[key] = f[key] || null;
        }
        queryParams['page'] = this.page() > 0 ? String(this.page()) : null;
        queryParams['pageSize'] = this.pageSize() !== 25 ? String(this.pageSize()) : null;
        // replaceUrl: filterjusteringar (särskilt fritext) ska inte spamma browser-historiken per tangenttryck
        this.router.navigate([], { relativeTo: this.route, queryParams, replaceUrl: true });
        this.loadIncidents();
    }

    protected onPageChange(event: PageEvent): void {
        this.page.set(event.pageIndex);
        this.pageSize.set(event.pageSize);
        this.syncUrlAndLoad();
    }

    protected onClearFilters(): void {
        this.filterForm.reset({ status: '', severity: '', assignee: '', ciId: '', slaState: '', search: '', createdAfter: '', createdBefore: '', sortBy: 'created_at', sortDir: 'desc' });
    }

    private loadIncidents(): void {
        this.loading.set(true);
        this.incidentService.list(this.buildFilter()).subscribe({
            next: (result) => {
                this.incidents.set(result.incidents);
                this.totalCount.set(result.total_count);
                this.loading.set(false);
            },
            error: () => {
                this.loading.set(false);
            }
        });
    }

    // Utan denna: backendens 400/409-fel (t.ex. ogiltig lifecycle-övergång) svaldes helt tyst -
    // knappen såg ut att inte göra något alls, ingen felindikation någonstans.
    private showError(err: { error?: { detail?: string } }, fallback: string): void {
        this.snackBar.open(err?.error?.detail || fallback, 'Dismiss', { duration: 5000 });
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
            },
            error: (err) => this.showError(err, 'Could not create incident.'),
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
            },
            error: (err) => this.showError(err, 'Could not add update.'),
        });
    }

    protected onAcceptSeverity(incidentId: number): void {
        this.incidentService.acceptSeverity(incidentId).subscribe({
            next: () => this.loadIncidents(),
            error: (err) => this.showError(err, 'Could not accept suggested severity.'),
        });
    }

    protected onAcceptStatus(incidentId: number): void {
        this.incidentService.acceptStatus(incidentId).subscribe({
            next: () => this.loadIncidents(),
            error: (err) => this.showError(err, 'Could not accept suggested status.'),
        });
    }

    protected onAssigneeChange(incidentId: number, assigneeUserId: number | null): void {
        this.incidentService.assign(incidentId, assigneeUserId).subscribe({
            next: () => this.loadIncidents(),
            error: (err) => this.showError(err, 'Could not update assignee.'),
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

    protected onViewUpdates(incidentId: number): void {
        // toggle: klick på samma rad igen stänger listan
        if (this.viewingUpdatesId() === incidentId) {
            this.viewingUpdatesId.set(null);
            return;
        }
        this.viewingUpdatesId.set(incidentId);
        this.incidentService.getUpdates(incidentId).subscribe({
            next: (updates) => this.incidentUpdates.set(updates)
        });
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
            },
            error: (err) => this.showError(err, 'Could not update incident.'),
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

    // Bygger CSS-klassnamnet till .chip-severity-low/medium/high/critical i styles.scss utifrån backend-strängen
    protected severityClass(severity: string): string {
        return `chip chip-severity-${(severity || '').toLowerCase()}`;
    }

    // Samma mönster för status (open/in_progress/resolved/closed)
    protected statusClass(status: string): string {
        return `chip chip-status-${(status || '').toLowerCase()}`;
    }

    // on_track=grön, at_risk=gul/orange, breached=röd, met=grön - återanvänder chip-severity-* färgerna
    protected slaClass(state: string): string {
        const map: Record<string, string> = { on_track: 'low', met: 'low', at_risk: 'medium', breached: 'critical' };
        return `chip chip-severity-${map[state] ?? ''}`;
    }
}

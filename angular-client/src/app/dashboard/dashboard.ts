import { Component, OnInit, computed, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { forkJoin } from 'rxjs';
import { IncidentService } from '../incidents/incident.service';
import { Incident } from '../incidents/incident';
import { CIService } from '../cis/ci.service';
import { CI } from '../cis/ci';
import { ChangeService } from '../changes/change.service';
import { Change } from '../changes/change';

interface Breakdown {
    key: string;
    count: number;
}

@Component({
    selector: 'app-dashboard',
    imports: [RouterLink, DatePipe, MatCardModule, MatIconModule, MatProgressSpinnerModule],
    templateUrl: './dashboard.html',
    styleUrl: './dashboard.scss',
})
export class Dashboard implements OnInit {
    protected readonly loading = signal(true);
    protected readonly incidents = signal<Incident[]>([]);
    protected readonly cis = signal<CI[]>([]);
    protected readonly changes = signal<Change[]>([]);

    // Alla siffror nedan är computed() från de tre listorna ovan - inget är hårdkodat,
    // de räknas om automatiskt varje gång incidents()/cis()/changes() uppdateras.
    protected readonly openIncidentsCount = computed(
        () => this.incidents().filter((i) => i.status !== 'resolved' && i.status !== 'closed').length
    );
    protected readonly highCriticalCount = computed(
        () => this.incidents().filter((i) => i.severity === 'high' || i.severity === 'critical').length
    );
    protected readonly totalCisCount = computed(() => this.cis().length);
    protected readonly recentChangesCount = computed(() => this.changes().length);

    protected readonly byStatus = computed<Breakdown[]>(() => this.breakdown(this.incidents(), (i) => i.status));
    protected readonly bySeverity = computed<Breakdown[]>(() => this.breakdown(this.incidents(), (i) => i.severity));

    // Nyast först - sorterar på created_at (ISO-sträng, funkar lexikografiskt) och tar de 5 senaste
    protected readonly recentIncidents = computed(() =>
        [...this.incidents()].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 5)
    );
    protected readonly recentChanges = computed(() => [...this.changes()].slice(-5).reverse());

    constructor(
        private incidentService: IncidentService,
        private ciService: CIService,
        private changeService: ChangeService,
    ) {}

    ngOnInit(): void {
        forkJoin({
            incidents: this.incidentService.list(),
            cis: this.ciService.list(),
            changes: this.changeService.list(),
        }).subscribe({
            next: ({ incidents, cis, changes }) => {
                this.incidents.set(incidents);
                this.cis.set(cis);
                this.changes.set(changes);
                this.loading.set(false);
            },
            error: () => this.loading.set(false),
        });
    }

    private breakdown<T>(items: T[], keyFn: (item: T) => string): Breakdown[] {
        const counts = new Map<string, number>();
        for (const item of items) {
            const key = keyFn(item) || 'unknown';
            counts.set(key, (counts.get(key) ?? 0) + 1);
        }
        return [...counts.entries()].map(([key, count]) => ({ key, count })).sort((a, b) => b.count - a.count);
    }

    protected severityClass(severity: string): string {
        return `chip chip-severity-${(severity || '').toLowerCase()}`;
    }

    protected statusClass(status: string): string {
        return `chip chip-status-${(status || '').toLowerCase()}`;
    }
}

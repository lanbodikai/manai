import {describe,it,expect,vi} from 'vitest';
import {render,screen,waitFor,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fixture from '../../contracts/examples/hardware-scenario.synthetic.json';
import {hardwarePayload,createHardwareApi,type HardwareScenario,type HardwareApi} from '../src/api/hardware';
import {HardwareScenarioPanel} from '../src/components/HardwareScenarioPanel';
import {DecisionOverview} from '../src/components/DecisionOverview';

const scenario=()=>hardwarePayload(structuredClone(fixture),'invented-browser');
const page=(s:HardwareScenario)=>({contract_version:'cpu-hardware-1' as const,scenario_id:s.scenario_id,dataset_version:s.dataset_version,synthetic:true,offset:0,limit:25,total:1,items:[{job_id:'invented-fit',status:'fits' as const,reason:'requested_resources_fit',recorded_gpu_hours:8,scheduler_hours:2,gpu_memory_category:'zero',requested_cores:2,requested_memory_mb:9000,memory_adjusted_cores:3}]});

describe('documented hardware feature',()=>{
  it('validates source, uncertainty and finite ordered values',()=>{
    expect(scenario().coverage.fitting_jobs).toBe(1);
    expect(()=>hardwarePayload(fixture,'stale')).toThrow();
    for(const mutate of [(x:HardwareScenario)=>{x.allocations[0].success_net_reference_usd.high=NaN;},
      (x:HardwareScenario)=>{x.coverage.fitting_jobs=100;},(x:HardwareScenario)=>{x.allocations[0].success_net_reference_usd.low=100;},
      (x:HardwareScenario)=>{(x as unknown as {cash_savings_verified:boolean}).cash_savings_verified=true;}]){
      const s=scenario();mutate(s);expect(()=>hardwarePayload(s,s.dataset_version)).toThrow();
    }
  });
  it('uses feature routes and rejects evidence from another scenario',async()=>{
    const s=scenario();const fetcher=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(s))).mockResolvedValueOnce(new Response(JSON.stringify({...page(s),scenario_id:'wrong'})));
    const api=createHardwareApi(fetcher,'http://local');await api.summary(s.dataset_version);
    expect(fetcher.mock.calls[0][0]).toContain('/api/cpu-hardware-scenario?dataset_version=invented-browser');
    await expect(api.jobs(s,'fits',0)).rejects.toThrow('does not match');
  });
  it('shows hardware scope and failure separately in existing tiles',()=>{
    const s=scenario();render(<DecisionOverview totalHours={32} price={2.5} windowLabel="Invented" outcomes={[]} hasOutcomes={false} review={null} hardware={s} onModel={()=>{}} onReview={()=>{}} disabled={false}/>);
    expect(screen.getByText('Simulated net reference benefit · full fitting population')).toBeVisible();
    expect(screen.getByText(/Successful replacement · unchanged runtime/)).toBeVisible();
    expect(screen.getByText(/Extra modeled cost if every fitting job needs a full GPU rerun/)).toBeVisible();
  });
  it('renders source-linked fit evidence without scaling a small pilot',async()=>{
    const s=scenario();const api:HardwareApi={summary:vi.fn(),jobs:vi.fn().mockResolvedValue(page(s))};const select=vi.fn();
    render(<HardwareScenarioPanel scenario={s} api={api} allocation="memory_adjusted" onAllocation={select}/>);
    expect(screen.getByText(/full fitting population, not the smaller pilot/)).toBeVisible();
    const user=userEvent.setup();await user.click(screen.getByText('Inspect resource-fit evidence'));
    expect(await screen.findByRole('link',{name:'Job invented-fit'})).toHaveAttribute('href',expect.stringContaining('invented-fit'));
    await user.selectOptions(screen.getByLabelText('CPU allocation'),'whole_node');expect(select).toHaveBeenCalledWith('whole_node');
    expect(screen.getByText(/not a confidence interval/)).toBeVisible();
  });
  it('does not display late evidence for a previous fit group',async()=>{
    const s=scenario();let resolveOld!:(value:ReturnType<typeof page>)=>void;
    const api:HardwareApi={summary:vi.fn(),jobs:vi.fn().mockImplementationOnce(()=>new Promise(resolve=>{resolveOld=resolve;})).mockResolvedValue({...page(s),total:0,items:[]})};
    render(<HardwareScenarioPanel scenario={s} api={api} allocation="memory_adjusted" onAllocation={()=>{}}/>);
    const user=userEvent.setup();await user.click(screen.getByText('Inspect resource-fit evidence'));
    await user.selectOptions(screen.getByLabelText('Resource-fit group'),'unresolved');
    await screen.findByText('0 jobs in this group.');resolveOld(page(s));
    await waitFor(()=>expect(screen.queryByRole('link',{name:'Job invented-fit'})).not.toBeInTheDocument());
  });
});

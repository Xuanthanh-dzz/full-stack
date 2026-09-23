using AsyncControlDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static async Task Main(){
using var cancel=new CancellationTokenSource();cancel.Cancel();int seen=0;var generator=new ReportGenerator();var task=generator.GenerateAsync(5,_=>seen++,cancel.Token);await ThrowsAsync<OperationCanceledException>(()=>task);Check(task.IsCanceled&&seen==0,"pre-cancel");
using var next=new CancellationTokenSource();seen=0;await ThrowsAsync<OperationCanceledException>(()=>generator.GenerateAsync(5,n=>{seen++;if(n==2)next.Cancel();},next.Token));Check(seen==2,"cancel checkpoint");var tcs=new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);await ThrowsAsync<TimeoutException>(()=>tcs.Task.WaitAsync(TimeSpan.Zero));Check(!tcs.Task.IsCompleted,"timeout canceled underlying");tcs.SetResult(7);Check(await tcs.Task==7,"underlying completion");
}
}

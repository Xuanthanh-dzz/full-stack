using DelegateDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
var small=new Order("A",1m);bool called=false;var value=OrderProcessor.Calculate(small,static _=>false,_=>{called=true;return 1m;});Check(!called&&value.Payable==1m,"ineligible still invoked policy");
Throws<InvalidOperationException>(()=>OrderProcessor.Calculate(small,static _=>true,static _=>2m));
var trace=new List<int>();Action audit=()=>trace.Add(1);audit+=()=>throw new InvalidOperationException();audit+=()=>trace.Add(3);Throws<InvalidOperationException>(audit);Check(trace.Count==1&&trace[0]==1,"multicast fail fast");
Func<int> returns=()=>1;returns+=()=>2;Check(returns()==2,"last return");
}
}

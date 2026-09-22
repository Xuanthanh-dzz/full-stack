using ClosureDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
var a=CounterFactory.Create();var b=CounterFactory.Create();Check(a()==1&&a()==2&&b()==1,"factory isolation");int limit=2;Func<int,bool> rule=x=>x>=limit;limit=5;Check(!rule(3)&&rule(5),"captured storage");
var bad=new List<Func<int>>();for(int i=0;i<3;i++)bad.Add(()=>i);Check(bad.TrueForAll(f=>f()==3),"for capture");
}
}

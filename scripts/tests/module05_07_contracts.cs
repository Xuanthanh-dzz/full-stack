using ImmutableOrderDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
var input=new List<OrderLine>{new(){Sku="A",Quantity=1,UnitPrice=2m}};var draft=new OrderDraft{Id="A",Customer=new("C","Name"),Lines=input};input.Clear();Check(draft.Lines.Count==1,"defensive copy");var sent=draft.Submit();Check(draft.Status==OrderStatus.Draft&&sent.Status==OrderStatus.Submitted&&ReferenceEquals(draft.Lines,sent.Lines),"snapshot");Throws<InvalidOperationException>(()=>sent.AddLine(new(){Sku="B",Quantity=1,UnitPrice=1m}));
var bypass=sent with{Lines=[]};Check(bypass.Status==OrderStatus.Submitted&&bypass.Lines.Count==0,"documented public init limitation");Check(sent.Lines.Count==1,"with mutated source");
}
}
